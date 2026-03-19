from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Header, BackgroundTasks
from typing import Optional
import cv2
import numpy as np

from app.schemas.response import AnalyzeResponse, Zone, Summary, GeoRef
from app.services.preprocess import preprocess_image
from app.services.deeplab import get_vegetation_mask
from app.services.ndvi import calculate_vegetation_index
from app.services.fusion import fuse_mask_and_index
from app.services.postprocess import extract_zones_and_overlay
from app.utils.image_utils import encode_image_base64
from app.services.geo_extractor import extract_gps
from app.services.geo_mapper import create_bounds, convert_contour_to_geo
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_crop_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    field_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None)
):
    try:
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR) # BGR
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
            
        # Extract Geo metadata
        gps_info = extract_gps(contents)
        # Preprocess
        prep_data = preprocess_image(image)
        
        # Inference
        mask_data = get_vegetation_mask(prep_data["rgb"])
        veg_mask = mask_data["veg_mask"]
        
        # NDVI
        index_data = calculate_vegetation_index(prep_data["red"], prep_data["green"], prep_data["blue"])
        index_map = index_data["index_map"]
        
        # Fusion
        final_index = fuse_mask_and_index(index_map, veg_mask)
        
        # Postprocess: thresholds, blobs, anomalies, and overlay map
        post_results = extract_zones_and_overlay(final_index, prep_data["rgb"])
        
        # Encode result image
        overlay_bgr = cv2.cvtColor(post_results["overlay_map"], cv2.COLOR_RGB2BGR)
        base64_img = encode_image_base64(overlay_bgr)
        
        # Geo processing
        geo_obj_dict = {"available": False}
        zones_data = post_results["zones"]
        
        if gps_info:
            logger.info("GPS detected: lat=%s, lon=%s", gps_info["lat"], gps_info["lon"])
            bounds = create_bounds(gps_info["lat"], gps_info["lon"])
            geo_obj_dict = {
                "available": True,
                "lat": gps_info["lat"],
                "lon": gps_info["lon"],
                "bounds": bounds
            }
            img_shape = prep_data["rgb"].shape
            
            geo_mapped_count = 0
            for z in zones_data:
                contour = z.pop("contour", [])
                if contour:
                    z["geo_coordinates"] = convert_contour_to_geo(contour, bounds, img_shape)
                    geo_mapped_count += 1
            logger.info("Geo mapping applied to %d zones", geo_mapped_count)
        else:
            logger.info("Geo unavailable – fallback to image-only mode")
            for z in zones_data:
                z.pop("contour", None)

        # Format response
        summary_obj = Summary(**post_results["summary"])
        zones_obj = [Zone(**z) for z in zones_data]
        geo_obj = GeoRef(**geo_obj_dict)
        
        # Database & Cloud persistence side-effect
        if field_id and user_id and authorization:
            try:
                from supabase import create_client, ClientOptions
                from app.core.config import settings
                from app.utils.s3_utils import upload_image_to_s3
                
                # Clone secure Supabase instance carrying user's live JWT auth
                jwt_token = authorization.split(" ")[1] if " " in authorization else authorization
                user_client = create_client(
                    settings.SUPABASE_URL, 
                    settings.SUPABASE_KEY, 
                    options=ClientOptions(headers={"Authorization": f"Bearer {jwt_token}"})
                )
                
                # Secure S3 Bucket Uploads
                original_url = upload_image_to_s3(contents, folder="originals")
                
                _, buffer = cv2.imencode('.jpg', overlay_bgr)
                overlay_url = upload_image_to_s3(buffer.tobytes(), folder="overlays")
                
                # Construct Scan ORM
                scan_res = user_client.table("scans").insert({
                    "field_id": field_id,
                    "user_id": user_id,
                    "image_url": original_url,
                    "overlay_url": overlay_url,
                    "healthy_pct": summary_obj.healthy,
                    "moderate_pct": summary_obj.moderate,
                    "severe_pct": summary_obj.severe,
                    "total_zones": summary_obj.total_zones
                }).execute()
                
                # Cascade into zone logs
                if scan_res.data:
                    scan_id = scan_res.data[0]["id"]
                    db_zones = []
                    for z in zones_data:
                        db_zones.append({
                            "scan_id": scan_id,
                            "zone_index": z.get("zone_id"),
                            "severity": z.get("severity"),
                            "health_score": z.get("health_score"),
                            "area": z.get("area"),
                            "issue": z.get("issue"),
                            "recommendation": z.get("recommendation"),
                            "geo_coordinates": z.get("geo_coordinates", [])
                        })
                    if db_zones:
                        user_client.table("zones").insert(db_zones).execute()
                        logger.info("Successfully persisted Scan and %d Zones to Supabase", len(db_zones))
                        
                    # Queue the background report compiler
                    from app.services.report_generator import generate_and_upload_report
                    background_tasks.add_task(
                        generate_and_upload_report,
                        scan_id=scan_id,
                        user_id=user_id,
                        field_id=field_id,
                        summary=post_results["summary"],
                        zones=zones_data,
                        user_client=user_client
                    )

            except Exception as db_err:
                logger.error(f"Failed backend DB linkage: {db_err}")

        return AnalyzeResponse(
            status="success",
            scan_id=scan_id if 'scan_id' in locals() else None,
            map=base64_img,
            geo=geo_obj,
            summary=summary_obj,
            zones=zones_obj
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/scan/{scan_id}", response_model=AnalyzeResponse)
async def analyze_existing_scan(
    scan_id: str,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """
    Trigger AI analysis on an existing scan that was ingested via Machine-to-Machine API.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
        
    try:
        from supabase import create_client, ClientOptions
        from app.core.config import settings
        from app.utils.s3_utils import upload_image_to_s3
        import urllib.request
        
        jwt_token = authorization.split(" ")[1] if " " in authorization else authorization
        user_client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_KEY, 
            options=ClientOptions(headers={"Authorization": f"Bearer {jwt_token}"})
        )
        
        # 1. Fetch scan record
        scan_res = user_client.table("scans").select("*").eq("id", scan_id).execute()
        if not scan_res.data:
            raise HTTPException(status_code=404, detail="Scan not found")
            
        scan_record = scan_res.data[0]
        image_url = scan_record.get("image_url")
        field_id = scan_record.get("field_id")
        user_id = scan_record.get("user_id") # Note: M2M might not set user_id correctly if not passed, but let's assume it's linked
        
        if not image_url:
            raise HTTPException(status_code=400, detail="Scan does not have an image URL")
            
        # 2. Download image
        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            contents = response.read()
            
        np_arr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR) # BGR
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file downloaded")
            
        # Extract Geo metadata
        gps_info = extract_gps(contents)
        # Preprocess
        prep_data = preprocess_image(image)
        
        # Inference
        mask_data = get_vegetation_mask(prep_data["rgb"])
        veg_mask = mask_data["veg_mask"]
        
        # NDVI
        index_data = calculate_vegetation_index(prep_data["red"], prep_data["green"], prep_data["blue"])
        index_map = index_data["index_map"]
        
        # Fusion
        final_index = fuse_mask_and_index(index_map, veg_mask)
        
        # Postprocess
        post_results = extract_zones_and_overlay(final_index, prep_data["rgb"])
        
        # Encode result image
        overlay_bgr = cv2.cvtColor(post_results["overlay_map"], cv2.COLOR_RGB2BGR)
        base64_img = encode_image_base64(overlay_bgr)
        
        # Geo processing
        geo_obj_dict = {"available": False}
        zones_data = post_results["zones"]
        
        if gps_info:
            bounds = create_bounds(gps_info["lat"], gps_info["lon"])
            geo_obj_dict = {
                "available": True, "lat": gps_info["lat"], "lon": gps_info["lon"], "bounds": bounds
            }
            img_shape = prep_data["rgb"].shape
            for z in zones_data:
                contour = z.pop("contour", [])
                if contour:
                    z["geo_coordinates"] = convert_contour_to_geo(contour, bounds, img_shape)
        else:
            for z in zones_data:
                z.pop("contour", None)

        summary_obj = Summary(**post_results["summary"])
        zones_obj = [Zone(**z) for z in zones_data]
        geo_obj = GeoRef(**geo_obj_dict)
        
        # 3. Secure S3 Bucket Uploads for overlay
        _, buffer = cv2.imencode('.jpg', overlay_bgr)
        overlay_url = upload_image_to_s3(buffer.tobytes(), folder="overlays")
        
        # 4. Update existing scan
        update_data = {
            "overlay_url": overlay_url,
            "status": "completed",
            "healthy_pct": summary_obj.healthy,
            "moderate_pct": summary_obj.moderate,
            "severe_pct": summary_obj.severe,
            "total_zones": summary_obj.total_zones
        }
        user_client.table("scans").update(update_data).eq("id", scan_id).execute()
        
        # 5. Insert zones
        db_zones = []
        for z in zones_data:
            db_zones.append({
                "scan_id": scan_id,
                "zone_index": z.get("zone_id"),
                "severity": z.get("severity"),
                "health_score": z.get("health_score"),
                "area": z.get("area"),
                "issue": z.get("issue"),
                "recommendation": z.get("recommendation"),
                "geo_coordinates": z.get("geo_coordinates", [])
            })
        if db_zones:
            user_client.table("zones").insert(db_zones).execute()
            
        # 6. Queue report
        if field_id:
            from app.services.report_generator import generate_and_upload_report
            background_tasks.add_task(
                generate_and_upload_report,
                scan_id=scan_id,
                user_id=user_id,
                field_id=field_id,
                summary=post_results["summary"],
                zones=zones_data,
                user_client=user_client
            )
            
        return AnalyzeResponse(
            status="success",
            scan_id=scan_id,
            map=base64_img,
            geo=geo_obj,
            summary=summary_obj,
            zones=zones_obj
        )

    except Exception as e:
        logger.error(f"Failed analysis of existing scan {scan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


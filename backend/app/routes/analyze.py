from fastapi import APIRouter, UploadFile, File, HTTPException
import cv2
import numpy as np

from app.schemas.response import AnalyzeResponse, Zone, Summary, GeoRef
from app.services.preprocess import preprocess_image
from app.services.deeplab import get_vegetation_mask
from app.services.ndvi import calculate_vegetation_index
from app.services.fusion import fuse_mask_and_index
from app.services.postprocess import extract_zones_and_overlay
from app.utils.image_utils import encode_image_base64
from app.utils.geo_utils import extract_gps_info

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_crop_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR) # BGR
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
            
        # Extract Geo metadata
        geo_info = extract_gps_info(contents)
        
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
        
        # Format response
        summary_obj = Summary(**post_results["summary"])
        zones_obj = [Zone(**z) for z in post_results["zones"]]
        geo_obj = GeoRef(**geo_info)
        
        return AnalyzeResponse(
            status="success",
            map=base64_img,
            geo=geo_obj,
            summary=summary_obj,
            zones=zones_obj
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import Optional
from datetime import datetime
import logging
from app.utils.s3_utils import upload_image_to_s3
from app.core.database import supabase

logger = logging.getLogger(__name__)

router = APIRouter()

# Cache to keep track of last frame time to throttle
LAST_FRAME_TIME: dict[str, datetime] = {}
FRAME_RATE_LIMIT_SEC = 2.0

@router.post("/ingest/frame")
async def ingest_frame(
    image: UploadFile = File(...),
    device_id: str = Form(...),
    timestamp: Optional[str] = Form(None),
    field_id: Optional[str] = Form(None),
    gps_lat: Optional[float] = Form(None),
    gps_lon: Optional[float] = Form(None),
    user_id: Optional[str] = Form(None)
):
    """
    Continuous machine-to-machine frame ingestion.
    Does NOT trigger AI analysis. Captures frames at a controlled rate and stores them safely in Supabase.
    """
    now = datetime.now()
    
    # Frame rate control
    last_time = LAST_FRAME_TIME.get(device_id)
    if last_time and (now - last_time).total_seconds() < FRAME_RATE_LIMIT_SEC:
        logger.info(f"Frame dropped for {device_id} (Rate limit exceeded)")
        return {"status": "dropped", "reason": "rate limit exceeded"}
        
    LAST_FRAME_TIME[device_id] = now
    
    try:
        contents = await image.read()
        logger.info(f"Frame received from {device_id}. Size: {len(contents)} bytes")
        
        # Generate S3 URL securely
        s3_url = upload_image_to_s3(contents, folder=f"ingest/{device_id}")
        
        # Determine format timestamp
        frame_time = timestamp or now.isoformat()
        
        # Base metadata for the scan
        scan_data = {
            "image_url": s3_url,
            "timestamp": frame_time,
            "healthy_pct": 0,    
            "moderate_pct": 0,
            "severe_pct": 0,
            "total_zones": 0
        }
        
        if field_id:
            scan_data["field_id"] = field_id
        if user_id:
            scan_data["user_id"] = user_id

        # ATTEMPT 1: Insert with premium feature columns (status/device_id)
        # We try this first to support the advanced UI.
        premium_data = {**scan_data, "status": "pending_analysis", "device_id": device_id}
        
        try:
            res = supabase.table("scans").insert(premium_data).execute()
        except Exception as e:
            error_str = str(e)
            if "device_id" in error_str or "status" in error_str:
                logger.warning("Database schema out of sync. Falling back to basic ingestion.")
                logger.warning("MIGRATION REQUIRED: Run 'ALTER TABLE scans ADD COLUMN status TEXT; ALTER TABLE scans ADD COLUMN device_id TEXT;' in your Supabase SQL Editor.")
                # FALLBACK: Insert only compatible columns
                res = supabase.table("scans").insert(scan_data).execute()
            else:
                # Rethrow unexpected DB errors
                raise e
        
        if res.data:
            scan_id = res.data[0]["id"]
            logger.info(f"Storage success: scan_id={scan_id}")
            return {
                "status": "success", 
                "scan_id": scan_id, 
                "image_url": s3_url,
                "frame_time": frame_time,
                "schema_warning": "status/device_id columns missing. Features limited until SQL migration is run." if "status" not in res.data[0] else None
            }
        else:
            logger.error("Failed to insert scan metadata into Supabase")
            raise HTTPException(status_code=500, detail="Database insertion failed")
            
    except Exception as e:
        logger.error(f"Storage failure for {device_id}: {str(e)}")
        # Provide the user with a direct hint in the API response 500
        hint = ""
        if "device_id" in str(e) or "status" in str(e):
            hint = " [MIGRATION REQUIRED: Run 'ALTER TABLE scans ADD COLUMN status TEXT DEFAULT 'completed'; ALTER TABLE scans ADD COLUMN device_id TEXT;' in Supabase SQL editor]"
        raise HTTPException(status_code=500, detail=str(e) + hint)


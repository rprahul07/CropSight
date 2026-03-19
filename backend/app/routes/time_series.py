from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from app.services.time_series import compare_scans
from app.services.time_series import compare_scans
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def get_user_client(auth_header: Optional[str]):
    if not auth_header:
        from app.core.database import supabase
        return supabase
    from supabase import create_client, ClientOptions
    from app.core.config import settings
    token = auth_header.split(" ")[1] if " " in auth_header else auth_header
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
        options=ClientOptions(headers={"Authorization": f"Bearer {token}"})
    )

class FieldCreate(BaseModel):
    user_id: str
    name: str

class FieldResponse(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: str

@router.post("/fields", response_model=FieldResponse)
async def create_field(field_data: FieldCreate, authorization: Optional[str] = Header(None)):
    try:
        user_client = get_user_client(authorization)
        response = user_client.table("fields").insert({
            "user_id": field_data.user_id,
            "name": field_data.name
        }).execute()
        
        if len(response.data) == 0:
            raise HTTPException(status_code=400, detail="Failed to create field.")
            
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating field: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fields")
async def get_fields(user_id: str, authorization: Optional[str] = Header(None)):
    try:
        user_client = get_user_client(authorization)
        response = user_client.table("fields").select("*").eq("user_id", user_id).execute()
        return {"fields": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_dashboard_stats(user_id: str, authorization: Optional[str] = Header(None)):
    try:
        user_client = get_user_client(authorization)
        response = user_client.table("scans").select("*").eq("user_id", user_id).execute()
        scans = response.data
        
        if not scans:
            return {
                "total_scans": 0,
                "avg_healthy_pct": 0,
                "avg_moderate_pct": 0,
                "avg_severe_pct": 0,
                "total_zones": 0
            }
            
        total_scans = len(scans)
        avg_healthy_pct = float(sum([s.get("healthy_pct", 0) for s in scans]) / total_scans)
        avg_moderate_pct = float(sum([s.get("moderate_pct", 0) for s in scans]) / total_scans)
        avg_severe_pct = float(sum([s.get("severe_pct", 0) for s in scans]) / total_scans)
        total_zones = sum([s.get("total_zones", 0) for s in scans])
        
        return {
            "total_scans": total_scans,
            "avg_healthy_pct": round(avg_healthy_pct, 2),
            "avg_moderate_pct": round(avg_moderate_pct, 2),
            "avg_severe_pct": round(avg_severe_pct, 2),
            "total_zones": total_zones
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fields/{field_id}/scans")
async def get_field_scans(field_id: str, authorization: Optional[str] = Header(None)):
    try:
        user_client = get_user_client(authorization)
        response = user_client.table("scans").select("*").eq("field_id", field_id).order("timestamp", desc=True).execute()
        return {"scans": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fields/{field_id}/compare")
async def compare_field_scans(field_id: str, prev_id: str, curr_id: str, authorization: Optional[str] = Header(None)):
    """
    Given two scan UUIDs, fetch them from Supabase and run the heuristic comparison.
    """
    try:
        user_client = get_user_client(authorization)
        prev_res = user_client.table("scans").select("*").eq("id", prev_id).execute()
        curr_res = user_client.table("scans").select("*").eq("id", curr_id).execute()

        if len(prev_res.data) == 0 or len(curr_res.data) == 0:
            raise HTTPException(status_code=404, detail="One or more scans not found")

        prev_scan = prev_res.data[0]
        curr_scan = curr_res.data[0]
        
        # We assume scans contain healthy_pct, moderate_pct, severe_pct.
        # Our SQL schema mapped these as numeric. Let's build the dict for our heuristic function.
        prev_dict = {
            "healthy_pct": float(prev_scan.get("healthy_pct", 0) or 0),
            "moderate_pct": float(prev_scan.get("moderate_pct", 0) or 0),
            "severe_pct": float(prev_scan.get("severe_pct", 0) or 0)
        }
        
        curr_dict = {
            "healthy_pct": float(curr_scan.get("healthy_pct", 0) or 0),
            "moderate_pct": float(curr_scan.get("moderate_pct", 0) or 0),
            "severe_pct": float(curr_scan.get("severe_pct", 0) or 0)
        }

        insights = compare_scans(prev_dict, curr_dict)
        return {"status": "success", "field_id": field_id, "comparison": insights}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{scan_id}")
async def get_scan_report(scan_id: str, authorization: Optional[str] = Header(None)):
    """
    Retrieves the generated HTML report URL from the scans table.
    """
    try:
        user_client = get_user_client(authorization)
        res = user_client.table("scans").select("id, timestamp, report_url").eq("id", scan_id).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Scan not found or unauthorized.")
            
        scan_record = res.data[0]
        
        return {
            "status": "success",
            "scan_id": scan_record.get("id"),
            "generated_at": scan_record.get("timestamp"),
            "report_url": scan_record.get("report_url")
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error retrieving scan report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/report/compare/{prev_id}/{curr_id}", response_class=HTMLResponse)
async def get_comparison_report(prev_id: str, curr_id: str, authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    """
    Dynamically generates and exclusively returns a comparison HTML payload visualizing the insights mapping.
    """
    try:
        auth_str = authorization or (f"Bearer {token}" if token else None)
        user_client = get_user_client(auth_str)
        
        prev_res = user_client.table("scans").select("*").eq("id", prev_id).execute()
        curr_res = user_client.table("scans").select("*").eq("id", curr_id).execute()

        if not prev_res.data or not curr_res.data:
            raise HTTPException(status_code=404, detail="One or more scans missing.")

        prev_scan = prev_res.data[0]
        curr_scan = curr_res.data[0]

        prev_dict = {
            "healthy_pct": float(prev_scan.get("healthy_pct", 0) or 0),
            "moderate_pct": float(prev_scan.get("moderate_pct", 0) or 0),
            "severe_pct": float(prev_scan.get("severe_pct", 0) or 0)
        }
        curr_dict = {
            "healthy_pct": float(curr_scan.get("healthy_pct", 0) or 0),
            "moderate_pct": float(curr_scan.get("moderate_pct", 0) or 0),
            "severe_pct": float(curr_scan.get("severe_pct", 0) or 0)
        }

        insights = compare_scans(prev_dict, curr_dict)
        
        trend = insights.get("trend", "UNKNOWN")
        trend_color = "#2E7D32" if trend in ["IMPROVING", "RECOVERY"] else ("#f44336" if trend in ["DETERIORATION", "WORSENING"] else "#ff9800")
        
        insight_list = insights.get('insights') or []
        display_message = insight_list[0].get('message') if insight_list else 'No critical thresholds reached. Crops maintained structural stability.'

        # Assemble HTML dynamically
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>CropSight Comparison Report</title>
            <style>
                body {{ font-family: 'Inter', sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #2E7D32; border-bottom: 2px solid #2E7D32; padding-bottom: 10px; }}
                .meta {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                .summary-stats {{ display: flex; gap: 20px; margin-bottom: 30px; }}
                .stat-box {{ flex: 1; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ddd; }}
                .health-title {{ font-size: 0.9em; font-weight: bold; color: #666; }}
                .insight-box {{ background-color: {trend_color}11; border-left: 5px solid {trend_color}; padding: 15px; margin: 30px 0; }}
                .print-btn {{ position: fixed; top: 20px; right: 20px; background-color: #2E7D32; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .print-btn:hover {{ background-color: #1b5e20; }}
                @media print {{
                    .no-print {{ display: none !important; }}
                    body {{ margin: 0; padding: 0; }}
                }}
            </style>
        </head>
        <body>
            <button class="print-btn no-print" onclick="window.print()">📥 Download PDF</button>

            <h1>Scan Comparison Report</h1>
            <div class="meta">
                <p><strong>Baseline Scan:</strong> {prev_id} ({prev_scan.get('timestamp')})</p>
                <p><strong>Recent Scan:</strong> {curr_id} ({curr_scan.get('timestamp')})</p>
            </div>
            
            <div class="insight-box">
                <h3 style="color: {trend_color}; margin-top: 0;">AI Synthesis: {trend}</h3>
                <p>{display_message}</p>
            </div>

            <h2>Side-by-Side Health Delta</h2>
            <div class="summary-stats">
                <div class="stat-box">
                    <div class="health-title">Baseline Healthy Area</div>
                    <h2>{prev_dict['healthy_pct']}%</h2>
                </div>
                <div class="stat-box">
                    <div class="health-title">Recent Healthy Area</div>
                    <h2>{curr_dict['healthy_pct']}%</h2>
                </div>
                <div class="stat-box" style="background-color: {trend_color}22;">
                    <div class="health-title">Net Change</div>
                    <h2 style="color: {trend_color}">{curr_dict['healthy_pct'] - prev_dict['healthy_pct']:.1f}%</h2>
                </div>
            </div>

            <div style="margin-top: 50px; text-align: center; font-size: 0.9em; color: #777;">
                <p>Generated securely by CropSight Autonomous Engine.</p>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error compiling comparative report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


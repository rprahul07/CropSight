import datetime
import logging
import uuid
from typing import Dict, Any, List
from app.utils.s3_utils import upload_image_to_s3
from supabase import Client

logger = logging.getLogger(__name__)

def generate_and_upload_report(
    scan_id: str,
    user_id: str,
    field_id: str,
    summary: Dict[str, Any],
    zones: List[Dict[str, Any]],
    user_client: Client
):
    """
    Background Task: Compiles a HTML report from the image scan context, uploads it to S3,
    and binds the resulting URL back into the PostgreSQL `scans` table.
    """
    try:
        logger.info(f"Starting report generation for Scan ID: {scan_id}")
        
        # 1. Synthesize HTML Report Template
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine aggregate AI intelligence paragraph
        dominant_issue = "None"
        if zones:
            issues = [z.get("issue") for z in zones if z.get("severity") in ["HIGH", "SEVERE"]]
            if issues:
                dominant_issue = max(set(issues), key=issues.count)
                
        ai_insight = f"The field exhibits a general health distribution of {summary.get('healthy', 0)}% healthy crop. "
        if dominant_issue != "None":
            ai_insight += f"However, significant anomalies were detected. The primary localized concern is '{dominant_issue}'. Immediate intervention is advised in the severe zones."
        else:
            ai_insight += "No critical anomalies detected across the analyzed zones. Routine maintenance is sufficient."

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>CropSight Scan Report - {scan_id}</title>
            <style>
                body {{ font-family: 'Inter', sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #2E7D32; border-bottom: 2px solid #2E7D32; padding-bottom: 10px; }}
                .meta {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                .summary-stats {{ display: flex; gap: 20px; margin-bottom: 30px; }}
                .stat-box {{ flex: 1; padding: 15px; border-radius: 8px; text-align: center; color: white; }}
                .healthy {{ background: #4caf50; }}
                .moderate {{ background: #ff9800; }}
                .severe {{ background: #f44336; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
                th {{ background-color: #f8f9fa; }}
                .insight-box {{ background-color: #e8f5e9; border-left: 5px solid #2E7D32; padding: 15px; margin: 30px 0; }}
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

            <h1>CropSight Analytics Report</h1>
            <div class="meta">
                <p><strong>Scan ID:</strong> {scan_id}</p>
                <p><strong>Field ID:</strong> {field_id}</p>
                <p><strong>Generated At:</strong> {now_str}</p>
            </div>
            
            <div class="insight-box">
                <h3>🤖 AI Synthesized Insight</h3>
                <p>{ai_insight}</p>
            </div>

            <h2>Field Composition</h2>
            <div class="summary-stats">
                <div class="stat-box healthy">
                    <h3>Healthy</h3>
                    <h2>{summary.get('healthy', 0)}%</h2>
                </div>
                <div class="stat-box moderate">
                    <h3>Moderate Stress</h3>
                    <h2>{summary.get('moderate', 0)}%</h2>
                </div>
                <div class="stat-box severe">
                    <h3>Severe Stress</h3>
                    <h2>{summary.get('severe', 0)}%</h2>
                </div>
            </div>

            <h2>Zone Breakdown Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Zone</th>
                        <th>Health Score</th>
                        <th>Severity</th>
                        <th>Primary Issue</th>
                        <th>Actionable Recommendation</th>
                    </tr>
                </thead>
                <tbody>
        """

        for z in zones:
            html_content += f"""
                    <tr>
                        <td>Zone {z.get('zone_id', '?')}</td>
                        <td>{z.get('health_score', '?')}/100</td>
                        <td>{z.get('severity', 'Unknown')}</td>
                        <td>{z.get('issue', 'None')}</td>
                        <td>{z.get('recommendation', 'N/A')}</td>
                    </tr>
            """

        html_content += """
                </tbody>
            </table>
            
            <div style="margin-top: 50px; text-align: center; font-size: 0.9em; color: #777;">
                <p>Generated securely by CropSight Autonomous Engine.</p>
            </div>
        </body>
        </html>
        """

        # 2. Upload byte-encoded HTML directly to AWS S3
        # Use content-type hinting implicitly or set explicitly if upload_image_to_s3 supports it.
        # Since currently upload_image_to_s3 explicitly sets 'image/jpeg', 
        # let's write a generic `upload_file_to_s3` or just use the existing one but be aware of content-type.
        from app.utils.s3_utils import s3_client
        from app.core.config import settings
        
        file_key = f"reports/{user_id}/{field_id}/{scan_id}_report.html"
        
        try:
            s3_client.put_object(
                Bucket=settings.AWS_S3_BUCKET_NAME,
                Key=file_key,
                Body=html_content.encode('utf-8'),
                ContentType='text/html'
            )
            report_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
            logger.info(f"Report uploaded successfully to AWS S3: {report_url}")
            
            # 3. Synchronize `report_url` with PostgreSQL `scans` Row
            # Try to update the row. (If the schema lacks 'report_url', this will throw, which we catch gracefully)
            try:
                user_client.table("scans").update({"report_url": report_url}).eq("id", scan_id).execute()
                logger.info(f"Database sync complete for report on Scan: {scan_id}")
            except Exception as db_err:
                logger.warning(f"Failed to bind report_url onto PostgreSQL scan schema. Has the schema been updated? Error: {db_err}")

        except Exception as s3_err:
            logger.error(f"S3 Upload failure for report: {s3_err}")

    except Exception as e:
        logger.error(f"Failed critical report pipeline execution asynchronously: {e}")

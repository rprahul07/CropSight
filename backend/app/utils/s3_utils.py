import boto3
import uuid
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

s3_client = boto3.client(
    's3',
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

def upload_image_to_s3(file_bytes: bytes, folder: str = "uploads", content_type: str = "image/jpeg") -> str:
    """Uploads raw bytes to AWS S3 and returns the public URL."""
    try:
        file_name = f"{folder}/{uuid.uuid4().hex}.jpg"
        
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=file_name,
            Body=file_bytes,
            ContentType=content_type,
            # Adjust ACL if bucket allows public read natively
            # ACL='public-read' 
        )
        
        # Build URL (Assuming generic S3 endpoint)
        url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_name}"
        return url
        
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
        return None

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "stream-curator-audio")

settings = Settings()

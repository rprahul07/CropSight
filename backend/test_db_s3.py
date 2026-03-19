import os
from dotenv import load_dotenv

# Needs to be called before importing config logic
load_dotenv()
from app.core.config import settings
from app.core.database import supabase
from app.utils.s3_utils import upload_image_to_s3
import uuid

def test_s3():
    print("--- Testing AWS S3 ---")
    print(f"Bucket: {settings.AWS_S3_BUCKET_NAME}")
    print(f"Region: {settings.AWS_REGION}")
    print(f"Key loaded: {bool(settings.AWS_ACCESS_KEY_ID)}")
    
    dummy_data = b"hello this is a test image payload array"
    
    try:
        url = upload_image_to_s3(dummy_data, folder="tests")
        if url:
            print(f"✅ S3 SUCCESS! URL generated: {url}")
            return url
        else:
            print("❌ S3 UPLOAD FAILED! upload_image_to_s3 returned None")
            return None
    except Exception as e:
        print(f"❌ S3 EXCEPTION: {e}")
        return None

def test_supabase(test_s3_url):
    print("\n--- Testing Supabase PostgreSQL ---")
    print(f"URL: {settings.SUPABASE_URL}")
    print(f"Key loaded: {bool(settings.SUPABASE_KEY)}")
    
    try:
        # Check Auth first (If we have a valid user)
        # Note: Bypassing auth creation for the test script. 
        # Since we use the Anon key, RLS might block anonymous inserts! 
        # Wait, if analyze.py uses supabase.table("scans").insert(), it relies on the Global Supabase Client
        # The global Supabase client initializes using SUPABASE_KEY. 
        # If SUPABASE_KEY is the Anon key in .env, RLS blocks ALL anonymous inserts unless the RLS policy permits it!
        import jwt
        
        # Let's just fetch fields to see connection
        res = supabase.table("fields").select("*").limit(1).execute()
        print(f"✅ Database connection successful! Fields count: {len(res.data)}")
        
        if len(res.data) > 0:
            field = res.data[0]
            print(f"Found Field ID: {field['id']} - User UUID: {field['user_id']}")
            
            # ATTEMPT INSERT TO SCANS
            print("Attempting to insert a test SCAN record...")
            try:
                scan_res = supabase.table("scans").insert({
                    "field_id": field['id'],
                    "user_id": field['user_id'],
                    "image_url": test_s3_url or "http://test.com",
                    "overlay_url": test_s3_url or "http://test.com",
                    "healthy_pct": 50.0,
                    "moderate_pct": 30.0,
                    "severe_pct": 20.0,
                    "total_zones": 3
                }).execute()
                print(f"✅ Supabase Scans Insert SUCCESS! Scan ID created: {scan_res.data[0]['id']}")
            except Exception as insert_e:
                print(f"❌ SUPABASE INSERT EXCEPTION! (This means RLS or Schema is blocking it!): {insert_e}")
                
        else:
            print("❌ No Fields found in the database to test relational insert onto.")
            
    except Exception as e:
        print(f"❌ SUPABASE CONNECTION EXCEPTION: {e}")

if __name__ == "__main__":
    print("BEGIN DIAGNOSTIC...")
    s3_url = test_s3()
    test_supabase(s3_url)
    print("END DIAGNOSTIC")

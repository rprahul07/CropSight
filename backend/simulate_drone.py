import requests
import time
import os

# Configuration
API_URL = "http://localhost:8000/ingest/frame"
DEVICE_ID = "drone_001"
# --- CONFIGURE THESE TO MATCH YOUR SUPABASE ---
USER_ID = "5e7626b2-dd8d-4944-b092-b69c080cbc82" # Paste your User ID from Supabase Auth here
FIELD_ID = "49468e24-cbcf-4e1b-a6a0-205132783c2e" # Paste an existing Field ID from Supabase here
# ----------------------------------------------

def send_frame(image_path):
    print(f"Sending {image_path} to {API_URL}...")
    
    # Provide the Form Data
    data = {
        "device_id": DEVICE_ID,
        "field_id": FIELD_ID,
        "user_id": USER_ID,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "gps_lat": 34.0522,
        "gps_lon": -118.2437
    }
    
    # Provide the Image File
    try:
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            
            # Send the POST request
            response = requests.post(API_URL, data=data, files=files)
            
            if response.status_code == 200:
                print("Success:", response.json())
            else:
                print(f"Failed ({response.status_code}):", response.text)
                
    except Exception as e:
        print("Error sending frame:", e)

if __name__ == "__main__":
    # Feel free to change this to any real image you have locally
    test_image_path = "test_image.jpg" 
    
    # Create a dummy image if it doesn't exist just for testing
    if not os.path.exists(test_image_path):
        import numpy as np
        import cv2
        dummy = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(test_image_path, dummy)
        
    # Simulate a drone flying and taking pictures every 3 seconds
    for i in range(3):
        send_frame(test_image_path)
        print("Waiting for next frame...")
        time.sleep(3) # Pausing to respect the rate-limit we set in the backend!


import cv2
import numpy as np

def preprocess_image(image: np.ndarray) -> dict:
    """
    Standardize input for both ML and NDVI.
    Steps:
    - Resize to 1024x1024
    - Normalize [0, 1]
    - Extract channels (R, G, B)
    """
    # Resize -> 1024x1024
    resized = cv2.resize(image, (1024, 1024))
    
    # Extract channels - OpenCV reads as BGR
    b, g, r = cv2.split(resized)
    
    # Convert to RGB and normalize -> [0, 1]
    rgb_normalized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    red = r.astype(np.float32) / 255.0
    green = g.astype(np.float32) / 255.0
    blue = b.astype(np.float32) / 255.0

    return {
        "rgb": rgb_normalized,
        "red": red,
        "green": green,
        "blue": blue
    }

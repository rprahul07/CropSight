import base64
import cv2
import numpy as np

def encode_image_base64(image: np.ndarray) -> str:
    """Encode an OpenCV image (numpy array) to base64 string."""
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def decode_image_base64(base64_str: str) -> np.ndarray:
    """Decode a base64 string to OpenCV image."""
    img_data = base64.b64decode(base64_str)
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img

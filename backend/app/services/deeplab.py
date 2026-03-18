import numpy as np
import torch
from torchvision import transforms
from app.models.deeplab_model import deep_lab_v3_model

def get_vegetation_mask(rgb_normalized: np.ndarray) -> dict:
    """
    Generate vegetation mask and filter non-crop regions.
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    input_tensor = transform((rgb_normalized * 255).astype(np.uint8)).unsqueeze(0)
    
    mask_tensor = deep_lab_v3_model.predict(input_tensor)
    
    veg_mask = mask_tensor.cpu().numpy().astype(np.uint8)
    
    return {
        "veg_mask": veg_mask
    }

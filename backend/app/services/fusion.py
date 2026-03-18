import numpy as np

def fuse_mask_and_index(index_map: np.ndarray, veg_mask: np.ndarray, model_confidence: np.ndarray = None) -> np.ndarray:
    """
    Combine DL + NDVI
    Logic:
    final_index = index_map * veg_mask
    Optional weighted fusion:
    final = 0.7 * index_map + 0.3 * model_confidence
    """
    # If the Pre-trained Deep Learning model is unable to recognize aerial crop domains 
    # and returns a mostly empty mask (<5% of image), we gracefully fallback to creating a 
    # pseudo-mask using the ExG/NDVI baseline so the pipeline still outputs results.
    height, width = veg_mask.shape
    if np.sum(veg_mask) < (0.05 * height * width):
        veg_mask = (index_map > 0.05).astype(np.uint8)
        
    # Base logical fusion: retain index only where vegetation mask is 1
    final_index = index_map * veg_mask
    
    if model_confidence is not None:
        # Optional weighted fusion combining index and model certainty
        final_index = (0.7 * final_index + 0.3 * model_confidence) * veg_mask
        
    return final_index

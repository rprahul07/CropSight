import numpy as np

def calculate_vegetation_index(red: np.ndarray, green: np.ndarray, blue: np.ndarray, nir: np.ndarray = None) -> dict:
    """
    Logic:
    If NIR available -> NDVI
    Else -> ExG
    
    ExG = 2G - R - B
    NDVI = (NIR - Red) / (NIR + Red)
    """
    eps = 1e-8 # Prevent division by zero
    
    if nir is not None:
        index_map = (nir - red) / (nir + red + eps)
        # Normalize NDVI from [-1, 1] to [0, 1]
        index_map = (index_map + 1) / 2
    else:
        index_map = 2 * green - red - blue
        
        # Normalize ExG to [0, 1]
        exg_min, exg_max = index_map.min(), index_map.max()
        if exg_max > exg_min:
            index_map = (index_map - exg_min) / (exg_max - exg_min)
        else:
            index_map = np.zeros_like(index_map)
            
    index_map = np.clip(index_map, 0.0, 1.0)
    
    return {
        "index_map": index_map
    }

import numpy as np
from sklearn.cluster import MiniBatchKMeans

def apply_clustering(final_index: np.ndarray, n_clusters: int = 3) -> np.ndarray:
    """
    1. Clustering - MiniBatchKMeans(n_clusters=3)
    """
    valid_mask = final_index > 0
    valid_data = final_index[valid_mask].reshape(-1, 1)
    
    if len(valid_data) == 0:
        return np.zeros_like(final_index, dtype=np.int32)
        
    kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init=3)
    labels = kmeans.fit_predict(valid_data)
    
    centers = kmeans.cluster_centers_.flatten()
    sorted_idx = np.argsort(centers)
    mapping = {sorted_idx[i]: i for i in range(n_clusters)}
    
    mapped_labels = np.array([mapping[l] for l in labels])
    
    clustered_image = np.zeros_like(final_index, dtype=np.int32)
    clustered_image[valid_mask] = mapped_labels + 1
    
    return clustered_image

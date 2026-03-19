import cv2
import numpy as np
from app.services.recommendation import get_recommendation, get_issue

def extract_zones_and_overlay(final_index: np.ndarray, original_rgb: np.ndarray) -> dict:
    """
    1. Threshold final_index into Severe, Moderate, Healthy masks.
    2. Connected components to find zones.
    3. Calculate stats, assign labels.
    4. Detect anomalies.
    5. Overlay on original_rgb.
    """
    height, width = final_index.shape
    
    # 1. Thresholds
    severe_mask = ((final_index > 0) & (final_index <= 0.3)).astype(np.uint8)
    moderate_mask = ((final_index > 0.3) & (final_index <= 0.6)).astype(np.uint8)
    healthy_mask = (final_index > 0.6).astype(np.uint8)
    
    # Smoothing
    severe_mask = cv2.medianBlur(severe_mask, 5)
    moderate_mask = cv2.medianBlur(moderate_mask, 5)
    healthy_mask = cv2.medianBlur(healthy_mask, 5)
    
    segmented = np.zeros_like(final_index, dtype=np.uint8)
    segmented[severe_mask == 1] = 1
    segmented[moderate_mask == 1] = 2
    segmented[healthy_mask == 1] = 3
    
    zones = []
    total_area = np.sum(segmented > 0)
    
    summary = {
        "healthy": 0.0,
        "moderate": 0.0,
        "severe": 0.0,
        "total_zones": 0
    }
    
    total_severe_area = np.sum(severe_mask)
    total_moderate_area = np.sum(moderate_mask)
    total_healthy_area = np.sum(healthy_mask)
    
    if total_area > 0:
        summary["severe"] = round(float(total_severe_area / total_area * 100), 2)
        summary["moderate"] = round(float(total_moderate_area / total_area * 100), 2)
        summary["healthy"] = round(float(total_healthy_area / total_area * 100), 2)
        
    severity_map = {
        3: ("LOW", "Healthy"),
        2: ("MODERATE", "Moderate"),
        1: ("HIGH", "Severe")
    }
    
    overlay = (original_rgb * 255).astype(np.uint8).copy()
    
    color_map = {
        1: (255, 0, 0),    # Red for Severe
        2: (255, 255, 0),  # Yellow for Moderate
        3: (0, 255, 0)     # Green for Healthy
    }
    
    zone_id = 1
    zone_centroids = []
    
    for cluster_val, (sev_level, label) in severity_map.items():
        mask = (segmented == cluster_val).astype(np.uint8)
        num_labels, labels_im, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area > 1000:
                zone_mask = (labels_im == i)
                health_score = float(np.mean(final_index[zone_mask]))
                
                # Blend with overlay
                color = color_map[cluster_val]
                roi = overlay[zone_mask]
                blended = roi * 0.5 + np.array(color) * 0.5
                overlay[zone_mask] = blended.astype(np.uint8)
                
                # Boundaries
                zone_mask_uint8 = zone_mask.astype(np.uint8)
                contours, _ = cv2.findContours(zone_mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(overlay, contours, -1, color, 2)
                
                issue = get_issue(health_score, label)
                recommendation = get_recommendation(label)
                
                cx, cy = centroids[i]
                zone_centroids.append({"id": zone_id, "cx": cx, "cy": cy, "score": health_score})
                
                contour_list = contours[0].tolist() if len(contours) > 0 else []
                
                zones.append({
                    "zone_id": zone_id,
                    "health_score": round(health_score, 2),
                    "severity": sev_level,
                    "area": float(area),
                    "issue": issue,
                    "recommendation": recommendation,
                    "contour": contour_list
                })
                zone_id += 1
                
    summary["total_zones"] = len(zones)
    
    # Irrigation Anomaly Detection: Sharp variation between adjacent zones
    for i in range(len(zones)):
        for j in range(i+1, len(zones)):
            z1 = zone_centroids[i]
            z2 = zone_centroids[j]
            dist = np.sqrt((z1["cx"] - z2["cx"])**2 + (z1["cy"] - z2["cy"])**2)
            
            # If centroids are physically close and score diff is high
            if dist < 300 and abs(z1["score"] - z2["score"]) > 0.4:
                zones[i]["issue"] = "Uneven Irrigation detected"
                zones[j]["issue"] = "Uneven Irrigation detected"
                
    return {
        "zones": zones,
        "summary": summary,
        "overlay_map": overlay
    }

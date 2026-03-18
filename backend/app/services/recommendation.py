def get_recommendation(label: str) -> str:
    if label == "Severe":
        return "Increase irrigation immediately"
    elif label == "Moderate":
        return "Inspect soil nutrients or pests"
    else:
        return "No immediate action required"
        
def get_issue(health_score: float, label: str) -> str:
    if label == "Severe":
        return "Possible Water Stress"
    elif label == "Moderate":
        return "Nutrient Issue"
    else:
        return "Healthy"

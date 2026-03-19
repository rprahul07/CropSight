def compare_scans(previous_scan: dict, current_scan: dict) -> dict:
    """
    Compares two structural scans to determine crop deterioration or recovery.
    Expects dictionary containing 'healthy_pct', 'moderate_pct', 'severe_pct'.
    """
    if not previous_scan or not current_scan:
        return {"status": "error", "message": "Incomplete data for comparison."}
    
    # Calculate global deltas
    delta_healthy = round(current_scan.get('healthy_pct', 0) - previous_scan.get('healthy_pct', 0), 2)
    delta_severe = round(current_scan.get('severe_pct', 0) - previous_scan.get('severe_pct', 0), 2)
    
    insights = []
    
    # Logic for trend analysis
    if delta_severe > 5.0:
        insights.append({
            "type": "DETERIORATION",
            "message": f"Critical: Severe crop stress has increased by {delta_severe}% since the last scan.",
            "urgency": "high"
        })
    elif delta_severe < -5.0:
        insights.append({
            "type": "RECOVERY",
            "message": f"Positive: Severe stress zones have reduced by {abs(delta_severe)}%.",
            "urgency": "low"
        })
        
    if delta_healthy > 5.0:
        insights.append({
            "type": "GROWTH",
            "message": f"Healthy foliage expanded by {delta_healthy}%.",
            "urgency": "info"
        })
        
    # Return overall trend
    overall_trend = "STABLE"
    if delta_severe > 3.0:
        overall_trend = "WORSENING"
    elif delta_healthy > 3.0 or delta_severe < -3.0:
        overall_trend = "IMPROVING"

    return {
        "trend": overall_trend,
        "delta_healthy": delta_healthy,
        "delta_severe": delta_severe,
        "insights": insights
    }

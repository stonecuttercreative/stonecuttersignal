# BEGIN stonecutter extension: scoring layer
from typing import List, Dict, Any
import statistics

def compute_signal_scores(panel_responses: List[Dict[str, Any]], final_scores: Dict[str, int]) -> Dict[str, Any]:
    """
    Compute confidence, diversity, and consensus metrics from provider responses.
    
    Args:
        panel_responses: List of provider response dicts with scores and telemetry
        final_scores: Final arbitrated scores dict
    
    Returns:
        Dict with confidence, diversity, consensus (0-100), and notes
    """
    if not panel_responses or not final_scores:
        return {
            "confidence": 60,
            "diversity": 10, 
            "consensus": 90,
            "notes": {"method": "no_data", "n_providers": 0}
        }
    
    # Extract score keys from final_scores
    score_keys = list(final_scores.keys())
    if not score_keys:
        return {
            "confidence": 60,
            "diversity": 10,
            "consensus": 90, 
            "notes": {"method": "no_score_keys", "n_providers": len(panel_responses)}
        }
    
    # Single provider case
    if len(panel_responses) == 1:
        return {
            "confidence": 60,
            "diversity": 10,
            "consensus": 90,
            "notes": {"method": "single_provider", "n_providers": 1}
        }
    
    # Collect latencies for downweighting
    latencies = []
    for resp in panel_responses:
        telemetry = resp.get("_telemetry", {})
        if telemetry and telemetry.get("latency_ms"):
            latencies.append(telemetry["latency_ms"])
    
    p75_latency = None
    if latencies:
        p75_latency = statistics.quantiles(latencies, n=4)[-1] if len(latencies) > 1 else latencies[0]
    
    # Calculate mean absolute deviation from median across all score keys
    total_dev = 0
    valid_keys = 0
    
    for key in score_keys:
        provider_scores = []
        weights = []
        
        for resp in panel_responses:
            scores = resp.get("scores", {})
            if key in scores and isinstance(scores[key], (int, float)):
                provider_scores.append(float(scores[key]))
                
                # Apply latency downweighting
                weight = 1.0
                if p75_latency:
                    telemetry = resp.get("_telemetry", {})
                    if telemetry and telemetry.get("latency_ms", 0) > p75_latency:
                        weight = 0.9
                weights.append(weight)
        
        if len(provider_scores) >= 2:
            median_score = statistics.median(provider_scores)
            
            # Weighted mean absolute deviation
            weighted_devs = []
            for score, weight in zip(provider_scores, weights):
                weighted_devs.append(abs(score - median_score) * weight)
            
            if weighted_devs:
                avg_dev_for_key = sum(weighted_devs) / len(weighted_devs)
                total_dev += avg_dev_for_key
                valid_keys += 1
    
    if valid_keys == 0:
        return {
            "confidence": 60,
            "diversity": 10,
            "consensus": 90,
            "notes": {"method": "no_valid_keys", "n_providers": len(panel_responses)}
        }
    
    # Calculate final metrics
    avg_dev = total_dev / valid_keys
    
    confidence = max(0, min(100, round((1.0 - avg_dev / 100.0) * 100)))
    diversity = max(0, min(100, round(min(100, avg_dev))))
    consensus = max(0, min(100, round(100 - diversity)))
    
    return {
        "confidence": confidence,
        "diversity": diversity,
        "consensus": consensus,
        "notes": {
            "method": "mad_based", 
            "n_providers": len(panel_responses),
            "valid_keys": valid_keys,
            "avg_deviation": round(avg_dev, 2)
        }
    }
# END stonecutter extension
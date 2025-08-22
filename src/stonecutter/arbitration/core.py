# BEGIN stonecutter extension
from statistics import median
from typing import List, Dict, Any
from ..settings import settings

def _weighted_median(items: List[tuple[int, float]]) -> int:
    if not items:
        return 0
    # simple median ignoring weights for now to keep deterministic
    vals = [v for v,_w in items]
    vals.sort()
    mid = len(vals)//2
    return int(vals[mid]) if len(vals) % 2 == 1 else int((vals[mid-1] + vals[mid]) / 2)

def _provider_weight(name: str) -> float:
    return {
        "openai": settings.weight_openai,
        "claude": settings.weight_claude,
        "gemini": settings.weight_gemini,
        "grok": settings.weight_grok,
        "perplexity": settings.weight_perplexity,
        "mistral": settings.weight_mistral,
    }.get(name, 1.0)

def arbitrate(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not responses:
        raise ValueError("No responses to arbitrate")

    cluster = responses[0].get("cluster", "General Clarity")
    archetype = responses[0].get("archetype", "Guide")

    # collect per-score arrays with weights
    buckets: Dict[str, List[tuple[int, float]]] = {}
    all_claims: List[str] = []
    for r in responses:
        w = _provider_weight(r.get("_provider_name","unknown"))
        for k, v in r.get("scores", {}).items():
            buckets.setdefault(k, []).append((int(v), w))
        all_claims.extend(r.get("claims", []))

    final_scores = {k: _weighted_median(vw) for k, vw in buckets.items()}

    # simple agreement-based confidence
    # compute average absolute deviation from median across keys
    deviations = []
    for k, vw in buckets.items():
        med = final_scores[k]
        for v, _w in vw:
            deviations.append(abs(v - med))
    avg_dev = sum(deviations)/max(1, len(deviations))
    confidence = max(0.5, min(0.99, 1.0 - (avg_dev / 100.0)))

    contradictions = [c for c in all_claims if str(c).strip().upper().startswith("NOT:")]

    return {
        "cluster": cluster,
        "archetype": archetype,
        "scores": final_scores,
        "contradictions": contradictions,
        "confidence": round(confidence, 2),
        "story": responses[0].get("story",""),
    }
# END stonecutter extension
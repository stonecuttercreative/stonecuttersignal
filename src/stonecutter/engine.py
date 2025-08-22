# BEGIN stonecutter extension
import asyncio
from typing import Dict, Any, List
from .providers.registry import load_panel
from .arbitration.core import arbitrate
import logging

logger = logging.getLogger(__name__)

async def _run_panel(prompt: str) -> List[Dict[str, Any]]:
    panel = load_panel()
    async def call(m):
        try:
            out = await m.complete(prompt)
            # BEGIN stonecutter extension: provider tag
            out["_provider_name"] = getattr(m, "name", "unknown")
            # END stonecutter extension
            return out
        except Exception as e:
            logger.warning(f"Provider failed: {getattr(m,'name','unknown')} -> {e}")
            return {"_provider_name": getattr(m,"name","unknown"),
                    "cluster":"General Clarity","archetype":"Guide","story":"",
                    "scores":{"cultural_fit":50,"clarity":50,"emotional_resonance":50,
                              "differentiation":50,"conversation_fit":50},
                    "claims":["Provider error fallback"]}
    tasks = [call(m) for m in panel]
    return await asyncio.gather(*tasks)

# BEGIN stonecutter extension: telemetry bubble-up
def surface_telemetry(panel_out: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract provider telemetry for inclusion in final results."""
    provider_meta = []
    for r in panel_out:
        meta = {
            "provider": r.get("_provider_name"),
            "latency_ms": (r.get("_telemetry") or {}).get("latency_ms"),
            "model": (r.get("_telemetry") or {}).get("model"),
            "input_tokens": (r.get("_telemetry") or {}).get("input_tokens"),
            "output_tokens": (r.get("_telemetry") or {}).get("output_tokens"),
        }
        provider_meta.append(meta)
    return provider_meta
# END stonecutter extension

# in your existing run_signal flow, replace the old panel call with:
# panel_out = await _run_panel(prompt)
# arb = arbitrate(panel_out)
# END stonecutter extension
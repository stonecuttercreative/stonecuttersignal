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
            out["_provider_name"] = getattr(m, "name", "unknown")
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

# in your existing run_signal flow, replace the old panel call with:
# panel_out = await _run_panel(prompt)
# arb = arbitrate(panel_out)
# END stonecutter extension
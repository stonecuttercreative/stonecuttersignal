# BEGIN stonecutter extension
import asyncio
from typing import Dict, Any, List
from .providers.registry import load_panel
from .arbitration.core import arbitrate
import logging

logger = logging.getLogger(__name__)

# BEGIN fix: openai-live
async def _run_panel(prompt: str) -> List[Dict[str, Any]]:
    panel = load_panel()
    async def call(m):
        import time
        t0 = time.time()
        try:
            out = await m.complete(prompt)
            # Normalize telemetry fields
            out["_provider_name"] = getattr(m, "name", "unknown")
            out["_telemetry"] = {
                "model": out.get("model"),
                "latency_ms": out.get("latency_ms", int((time.time() - t0) * 1000)),
                "error": out.get("error"),
                "provider": out.get("provider", getattr(m, "name", "unknown"))
            }
            return out
        except Exception as e:
            logger.warning(f"Provider failed: {getattr(m,'name','unknown')} -> {e}")
            return {
                "_provider_name": getattr(m,"name","unknown"),
                "_telemetry": {
                    "model": None,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "error": f"provider_error: {type(e).__name__}: {e}",
                    "provider": getattr(m,"name","unknown")
                },
                "cluster":"General Clarity","archetype":"Guide","story":"",
                "scores":{"cultural_fit":50,"clarity":50,"emotional_resonance":50,
                          "differentiation":50,"conversation_fit":50},
                "claims":["Provider error fallback"]
            }
    tasks = [call(m) for m in panel]
    return await asyncio.gather(*tasks)
# END fix: openai-live

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

# BEGIN stonecutter live: evidence integration
from .data_sources.registry import load_sources
from .persistence.sqlite_store import save_evidence
from .settings import settings

async def _gather_evidence(intake) -> list[dict]:
    q = " ".join(filter(None, [intake.brand, intake.category, intake.concept]))[:180]
    items=[]
    for src in load_sources():
        try:
            items.extend(await src.fetch(q))
        except Exception:
            pass
    # de-duplicate by URL, cap items
    seen=set(); out=[]
    for e in items:
        u=e.get("url")
        if u and u not in seen:
            out.append(e); seen.add(u)
        if len(out) >= settings.evidence_max_items:
            break
    return out

# Wrap/extend build_prompt to include evidence bullets (keep existing behavior)
def build_prompt(intake) -> str:
    evidence_list = getattr(intake, "_evidence", [])
    evidence_txt = ""
    if evidence_list:
        bullets = [f"- {e.get('title','')}: {e.get('snippet','')}" for e in evidence_list]
        evidence_txt = "\nRecent context:\n" + "\n".join(bullets)
    
    # Basic prompt template - this should be replaced with actual template logic
    return f"""
Brand: {intake.brand}
Category: {intake.category}
Concept: {intake.concept}
Mode: {getattr(intake, 'mode', 'realtime')}
Audience: {getattr(intake, 'audience', '')}
Channels: {getattr(intake, 'channels', '')}
{evidence_txt}

Please analyze this campaign brief and provide diagnostic scores for cultural_fit, clarity, emotional_resonance, differentiation, and conversation_fit on a scale of 0-100.
"""

async def run_signal(raw_input: Dict[str, Any] | str) -> Dict[str, Any]:
    from types import SimpleNamespace
    
    # Parse intake
    if isinstance(raw_input, str):
        intake = SimpleNamespace(brand="Unknown", category="Unknown", concept=raw_input)
    else:
        intake = SimpleNamespace(**raw_input)

    # evidence fetch before panel
    intake._evidence = await _gather_evidence(intake)

    prompt = build_prompt(intake)
    
    # existing panel + arbitrate
    panel_out = await _run_panel(prompt)
    arb = arbitrate(panel_out)

    # Assemble run_record with telemetry
    import time, uuid
    run_record = {
        'id': str(uuid.uuid4()),
        'ts': int(time.time()),
        'timestamp': int(time.time()),
        'mode': getattr(intake, 'mode', 'realtime'),
        'brand': intake.brand,
        'category': intake.category,
        'concept': intake.concept,
        'audience': getattr(intake, 'audience', ''),
        'channels': getattr(intake, 'channels', ''),
        'evidence': intake._evidence,
        'scores': arb.get('scores', {}),
        'story': arb.get('story', ''),
        'providers': surface_telemetry(panel_out),
        'meta': {
            'signal_scores': {
                'confidence': arb.get('confidence', 50),
                'consensus': arb.get('consensus', 50),
                'diversity': arb.get('diversity', 50)
            }
        }
    }
    
    # Persist evidence
    if settings.persistence_enabled:
        from .persistence.sqlite_store import save_run
        save_evidence(run_record["id"], intake._evidence)
        save_run(run_record)

    return run_record
# END stonecutter live: evidence integration

# in your existing run_signal flow, replace the old panel call with:
# panel_out = await _run_panel(prompt)
# arb = arbitrate(panel_out)
# END stonecutter extension
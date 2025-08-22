# BEGIN stonecutter extension
import asyncio, random
from typing import Dict, Any

def _clip(x: int) -> int:
    return max(0, min(100, int(x)))

async def mock_complete(name: str, prompt: str) -> Dict[str, Any]:
    r = random.Random(hash(name + str(len(prompt))) & 0xffffffff)
    base = len(prompt) % 23
    jitter = r.randint(0, 6)
    await asyncio.sleep(0.02 + 0.01*jitter)
    scores = {
        "cultural_fit": _clip(70 + base - jitter),
        "clarity": _clip(65 + base),
        "emotional_resonance": _clip(68 + base + jitter),
        "differentiation": _clip(60 + base//2),
        "conversation_fit": _clip(64 + base - jitter//2),
    }
    if "Channels:" in prompt and "N/A" not in prompt:
        scores["distribution_fit"] = _clip(66 + base//2)
    return {
        "cluster": "General Clarity",
        "archetype": "Guide",
        "story": "Clear, grounded guidance with practical framing and minimal hype.",
        "scores": scores,
        "claims": ["Clarity over hype", "Grounded in lived context", "No specific coin promises"],
    }
# END stonecutter extension
# BEGIN stonecutter extension
from typing import Protocol, Dict, Any

class LLMProvider(Protocol):
    name: str
    async def complete(self, prompt: str, **kw) -> Dict[str, Any]:
        """
        Return JSON-like dict:
        {
          "cluster": str,
          "archetype": str,
          "story": str,
          "scores": {
            "cultural_fit": int, "clarity": int, "emotional_resonance": int,
            "differentiation": int, "conversation_fit": int,
            # optional
            "distribution_fit": int
          },
          "claims": [str, str, str]
        }
        """
        ...
# END stonecutter extension
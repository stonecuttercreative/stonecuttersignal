# BEGIN stonecutter extension: real Perplexity provider
from typing import Dict, Any
import json, asyncio, time
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
from ..settings import settings
from ._mock_util import mock_complete

PROMPT_WRAPPER = """You are a cultural diagnostics analyst.
Return STRICT JSON ONLY, no prose.
JSON schema:
{{
  "cluster": str,
  "archetype": str,
  "story": str,
  "scores": {{
    "cultural_fit": int, "clarity": int, "emotional_resonance": int,
    "differentiation": int, "conversation_fit": int{extra_score}
  }},
  "claims": [str, str, str]
}}
If you cite sources, DO NOT include prose—just produce the JSON.
Input:
{input_block}
"""

API_URL = "https://api.perplexity.ai/chat/completions"

class PerplexityProvider:
    name = "perplexity"

    async def complete(self, prompt: str, **kw) -> Dict[str, Any]:
        start = time.time()
        # Fallback if disabled or no key
        if not settings.enable_perplexity or not settings.perplexity_api_key or not HTTPX_AVAILABLE:
            mock_resp = await mock_complete(self.name, prompt)
            mock_resp.update({
                "provider": self.name,
                "model": None,
                "latency_ms": int((time.time() - start) * 1000),
                "error": None if settings.perplexity_api_key else "PERPLEXITY_API_KEY missing or httpx not installed",
            })
            return mock_resp

        extra = ', "distribution_fit": int' if ("Channels:" in prompt and "N/A" not in prompt) else ""
        wrapped = PROMPT_WRAPPER.format(extra_score=extra, input_block=prompt)
        try:
            headers = {
                "Authorization": f"Bearer {settings.perplexity_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": settings.perplexity_model,
                "messages": [
                    {"role": "system", "content": "Answer with strict JSON only."},
                    {"role": "user", "content": wrapped}
                ],
                "temperature": 0.4,
                "stream": False
            }

            # Use async client
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(API_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            # Perplexity returns OpenAI-style choices
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            try:
                parsed = json.loads(text)
            except Exception:
                # If model added extra prose, keep run stable via mock
                return await mock_complete(self.name, prompt)

            parsed["_telemetry"] = {
                "provider": self.name,
                "latency_ms": int((time.time() - start) * 1000),
                "model": settings.perplexity_model,
                # Perplexity may not return token counts consistently; leave None
                "input_tokens": None,
                "output_tokens": None,
            }
            return parsed

        except Exception as e:
            # Return mock with explicit error for diagnostics  
            mock_resp = await mock_complete(self.name, prompt)
            mock_resp.update({
                "provider": self.name,
                "model": None,
                "latency_ms": int((time.time() - start) * 1000),
                "error": f"perplexity_error: {type(e).__name__}: {e}",
            })
            return mock_resp
# END stonecutter extension
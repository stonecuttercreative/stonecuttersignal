# BEGIN stonecutter extension: real Gemini provider
from typing import Dict, Any
import json, asyncio, time
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
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
Input:
{input_block}
"""

class GeminiProvider:
    name = "gemini"

    async def complete(self, prompt: str, **kw) -> Dict[str, Any]:
        if not settings.enable_gemini or not settings.google_genai_key or not GEMINI_AVAILABLE:
            return await mock_complete(self.name, prompt)

        extra = ', "distribution_fit": int' if ("Channels:" in prompt and "N/A" not in prompt) else ""
        wrapped = PROMPT_WRAPPER.format(extra_score=extra, input_block=prompt)

        start = time.time()
        try:
            # Configure once per call (simple + safe here)
            genai.configure(api_key=settings.google_genai_key)

            # Gemini SDK is sync-ish; use thread executor to avoid blocking
            def _call():
                model = genai.GenerativeModel(settings.gemini_model)
                # We ask for JSON; some SDKs need a system prompt or MIME. Keep simple here.
                resp = model.generate_content(wrapped)
                # Extract plain text
                return resp.text if hasattr(resp, "text") else str(resp)

            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, _call)

            try:
                data = json.loads(text)
            except Exception:
                # If parsing fails (model added prose), fallback to mock to keep pipeline stable
                return await mock_complete(self.name, prompt)

            data["_telemetry"] = {
                "provider": self.name,
                "latency_ms": int((time.time() - start) * 1000),
                "model": settings.gemini_model,
                # Gemini SDK may not expose token counts here; leave None
                "input_tokens": None,
                "output_tokens": None,
            }
            return data
        except Exception:
            return await mock_complete(self.name, prompt)
# END stonecutter extension
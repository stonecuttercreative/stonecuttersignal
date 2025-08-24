# BEGIN stonecutter extension: real Claude provider
from typing import Dict, Any
import json, asyncio, time
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
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

class ClaudeProvider:
    name = "claude"

    async def complete(self, prompt: str, **kw) -> Dict[str, Any]:
        start = time.time()
        # Soft fallback if disabled or no key
        if not settings.enable_claude or not settings.anthropic_api_key or not ANTHROPIC_AVAILABLE:
            mock_resp = await mock_complete(self.name, prompt)
            mock_resp.update({
                "provider": self.name,
                "model": None,
                "latency_ms": int((time.time() - start) * 1000),
                "error": None if settings.anthropic_api_key else "ANTHROPIC_API_KEY missing or anthropic client not installed",
            })
            return mock_resp

        # Build wrapped prompt; include distribution_fit only when channels provided
        extra = ', "distribution_fit": int' if ("Channels:" in prompt and "N/A" not in prompt) else ""
        wrapped = PROMPT_WRAPPER.format(extra_score=extra, input_block=prompt)

        # Call Claude using the Messages API
        try:
            client = Anthropic(api_key=settings.anthropic_api_key)
            # Claude is not async; run in thread to avoid blocking
            def _call():
                msg = client.messages.create(
                    model=settings.claude_model,
                    max_tokens=800,
                    temperature=0.6,
                    messages=[{"role": "user", "content": wrapped}],
                )
                return msg
            loop = asyncio.get_running_loop()
            msg = await loop.run_in_executor(None, _call)

            # Extract text content
            content = "".join([b.text for b in msg.content if getattr(b, "type", "") == "text"])
            # Parse JSON strictly; if parse fails, fallback to mock
            try:
                data = json.loads(content)
            except Exception:
                return await mock_complete(self.name, prompt)

            # Telemetry
            data["_telemetry"] = {
                "provider": self.name,
                "latency_ms": int((time.time() - start) * 1000),
                "model": settings.claude_model,
                # token usage not always present; include when available
                "input_tokens": getattr(getattr(msg, "usage", None), "input_tokens", None),
                "output_tokens": getattr(getattr(msg, "usage", None), "output_tokens", None),
            }
            return data
        except Exception as e:
            # Return mock with explicit error for diagnostics
            mock_resp = await mock_complete(self.name, prompt)
            mock_resp.update({
                "provider": self.name,
                "model": None,
                "latency_ms": int((time.time() - start) * 1000),
                "error": f"anthropic_error: {type(e).__name__}: {e}",
            })
            return mock_resp
# END stonecutter extension
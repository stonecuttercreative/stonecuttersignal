# BEGIN fix: openai-live
import time
from typing import Dict, Any
from ..settings import settings
from ._mock_util import mock_complete

try:
    # Support either new OpenAI client or legacy import; prefer new
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False

class OpenAIProvider:
    name = "openai"

    async def complete(self, prompt: str, **kw) -> Dict[str, Any]:
        t0 = time.time()
        key = settings.openai_api_key
        model = settings.openai_model
        
        if not settings.enable_openai or not key or not _OPENAI_AVAILABLE:
            # MOCK path
            mock_resp = await mock_complete(self.name, prompt)
            mock_resp.update({
                "provider": self.name,
                "model": None,
                "latency_ms": int((time.time() - t0) * 1000),
                "error": None if key else "OPENAI_API_KEY missing or OpenAI client not installed",
            })
            return mock_resp
            
        try:
            client = OpenAI(api_key=key)
            # Use a small, safe call; adapt to your JSON protocol upstream
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt[:4000]}],
                temperature=0.2,
                max_tokens=256,
            )
            txt = resp.choices[0].message.content if resp and resp.choices else ""
            
            # Try to parse as JSON for structured output, fallback to text
            try:
                parsed = eval(txt) if txt.strip().startswith('{') else {"story": txt}
            except:
                parsed = {"story": txt}
                
            return {
                "provider": self.name,
                "model": model,
                "latency_ms": int((time.time() - t0) * 1000),
                "error": None,
                **parsed
            }
        except Exception as e:
            # Fallback but keep reason visible
            mock_resp = await mock_complete(self.name, prompt)
            mock_resp.update({
                "provider": self.name,
                "model": None,
                "latency_ms": int((time.time() - t0) * 1000),
                "error": f"openai_error: {type(e).__name__}: {e}",
            })
            return mock_resp
# END fix: openai-live
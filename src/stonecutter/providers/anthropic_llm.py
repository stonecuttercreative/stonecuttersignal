# BEGIN composite: env+providers
import time
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
from ..settings import settings

class ClaudeProvider:
    name = "claude"

    async def complete(self, prompt: str, **kw):
        t0 = time.time()
        if not settings.enable_claude or not settings.anthropic_api_key or not ANTHROPIC_AVAILABLE:
            return {"provider": self.name, "model": None, "latency_ms": int((time.time()-t0)*1000), "error": "anthropic_error: missing ANTHROPIC_API_KEY or anthropic client not installed"}

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        last_err = None
        for model in settings.claude_fallbacks:
            try:
                resp = client.messages.create(model=model, max_tokens=256, temperature=0.2,
                                              messages=[{"role":"user","content":prompt[:4000]}])
                txt = resp.content[0].text if getattr(resp,"content",None) else ""
                return {"provider": self.name, "model": model, "latency_ms": int((time.time()-t0)*1000), "output":{"text":txt}, "error": None}
            except anthropic.NotFoundError:
                last_err = f"anthropic_error: NotFound (model {model})"
                continue
            except Exception as e:
                last_err = f"anthropic_error: {type(e).__name__}: {e}"
                break
        return {"provider": self.name, "model": None, "latency_ms": int((time.time()-t0)*1000), "output":{"text":""}, "error": last_err or "anthropic_error: unknown"}
# END composite: env+providers
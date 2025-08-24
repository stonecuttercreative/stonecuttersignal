# BEGIN patch: perplexity+grok-live
import time
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
from ..settings import settings

XAI_URL = "https://api.x.ai/v1/chat/completions"

class GrokProvider:
    name = "grok"

    async def complete(self, prompt: str, **kw):
        t0 = time.time()
        key = settings.xai_api_key
        if not settings.enable_grok or not key or not HTTPX_AVAILABLE:
            return {"provider": self.name, "model": None, "latency_ms": int((time.time()-t0)*1000),
                    "error":"grok_error: missing XAI_API_KEY or httpx not installed"}

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        last_err = None

        async with httpx.AsyncClient(timeout=20) as client:
            for model in settings.grok_fallbacks:
                body = {"model": model,
                        "messages":[{"role":"user","content": prompt[:4000]}],
                        "temperature":0.2, "max_tokens":256}
                try:
                    r = await client.post(XAI_URL, headers=headers, json=body)
                    if r.status_code != 200:
                        last_err = f"grok_error: HTTP {r.status_code} {r.text[:140]}"
                        # Try next fallback if this looks like NotFound/Bad model
                        if r.status_code in (400,404):
                            continue
                        else:
                            break
                    data = r.json()
                    txt = (data.get("choices") or [{}])[0].get("message",{}).get("content","")
                    return {"provider": self.name, "model": model,
                            "latency_ms": int((time.time()-t0)*1000),
                            "output":{"text": txt}, "error": None}
                except Exception as e:
                    last_err = f"grok_error: {type(e).__name__}: {e}"
                    continue

        return {"provider": self.name, "model": None, "latency_ms": int((time.time()-t0)*1000),
                "output":{"text":""}, "error": last_err or "grok_error: unknown"}
# END patch: perplexity+grok-live
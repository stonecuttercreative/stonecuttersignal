# BEGIN composite: env+providers
import time
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
from ..settings import settings

PPLX_URL = "https://api.perplexity.ai/chat/completions"

class PerplexityProvider:
    name = "perplexity"

    async def complete(self, prompt: str, **kw):
        t0=time.time()
        key = settings.perplexity_api_key
        if not settings.enable_perplexity or not key or not HTTPX_AVAILABLE:
            return {"provider": self.name, "model": None, "latency_ms": int((time.time()-t0)*1000), "error":"perplexity_error: missing PERPLEXITY_API_KEY or httpx not installed"}

        headers={"Authorization": f"Bearer {key}", "Content-Type":"application/json"}
        last_err=None
        async with httpx.AsyncClient(timeout=20) as client:
            for model in settings.perplexity_fallbacks:
                try:
                    body={"model": model, "messages":[{"role":"user","content": prompt[:4000]}], "temperature":0.2, "max_tokens":256}
                    r = await client.post(PPLX_URL, headers=headers, json=body)
                    if r.status_code != 200:
                        last_err = f"perplexity_error: HTTP {r.status_code} {r.text[:120]}"
                        continue
                    data=r.json()
                    txt = data.get("choices",[{}])[0].get("message",{}).get("content","")
                    return {"provider": self.name, "model": model, "latency_ms": int((time.time()-t0)*1000), "output":{"text":txt}, "error": None}
                except Exception as e:
                    last_err=f"perplexity_error: {type(e).__name__}: {e}"
                    continue
        return {"provider": self.name, "model": None, "latency_ms": int((time.time()-t0)*1000), "output":{"text":""}, "error": last_err or "perplexity_error: unknown"}
# END composite: env+providers
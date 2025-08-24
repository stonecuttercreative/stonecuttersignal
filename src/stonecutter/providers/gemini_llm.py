# BEGIN composite: env+providers
import time
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
from ..settings import settings

class GeminiProvider:
    name = "gemini"

    async def complete(self, prompt: str, **kw):
        t0=time.time()
        key = settings.google_genai_key
        if not settings.enable_gemini or not key or not GEMINI_AVAILABLE:
            return {"provider": self.name, "model": None, "latency_ms": int((time.time()-t0)*1000), "error":"gemini_error: missing GOOGLE_GENAI_API_KEY/GOOGLE_API_KEY or google-generativeai not installed"}
        genai.configure(api_key=key)
        last_err=None
        for model in settings.gemini_fallbacks:
            try:
                m = genai.GenerativeModel(model)
                resp = m.generate_content(prompt[:4000])
                txt = resp.text or ""
                return {"provider": self.name, "model": model, "latency_ms": int((time.time()-t0)*1000), "output":{"text":txt}, "error": None}
            except Exception as e:
                last_err=f"gemini_error: {type(e).__name__}: {e}"
                continue
        return {"provider": self.name, "model": None, "latency_ms": int((time.time()-t0)*1000), "output":{"text":""}, "error": last_err or "gemini_error: unknown"}
# END composite: env+providers
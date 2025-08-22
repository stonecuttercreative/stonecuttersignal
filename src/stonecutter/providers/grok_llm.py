# BEGIN stonecutter extension: grok provider
from typing import Dict, Any
import time, asyncio
from ..settings import settings
from ._mock_util import mock_complete

class GrokProvider:
    name = "grok"

    async def complete(self, prompt: str, **kw) -> Dict[str, Any]:
        # Until xAI endpoint is wired, or if key is absent, use safe mock
        start = time.time()
        if not settings.enable_grok or not settings.xai_api_key:
            data = await mock_complete(self.name, prompt)
        else:
            # Placeholder: keep mock for now to avoid hard dependency.
            # Swap this block to a real httpx call when flipping live.
            data = await mock_complete(self.name, prompt)

        data.setdefault("_telemetry", {})
        data["_telemetry"].update({
            "provider": self.name,
            "latency_ms": int((time.time() - start) * 1000),
            "model": settings.grok_model,
            "input_tokens": None,
            "output_tokens": None,
        })
        return data
# END stonecutter extension: grok provider
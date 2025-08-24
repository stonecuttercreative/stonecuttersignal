# BEGIN stonecutter extension: grok provider
from typing import Dict, Any
import time, asyncio
from ..settings import settings
from ._mock_util import mock_complete

class GrokProvider:
    name = "grok"

    async def complete(self, prompt: str, **kw) -> Dict[str, Any]:
        start = time.time()
        
        if not settings.enable_grok or not settings.xai_api_key:
            # No key present - return mock with appropriate error
            data = await mock_complete(self.name, prompt)
            data.update({
                "provider": self.name,
                "model": None,
                "latency_ms": int((time.time() - start) * 1000),
                "error": None if settings.xai_api_key else "XAI_API_KEY missing",
            })
            return data
        else:
            # Key present but real endpoint not implemented yet
            data = await mock_complete(self.name, prompt)
            data.update({
                "provider": self.name,
                "model": None,
                "latency_ms": int((time.time() - start) * 1000),
                "error": "grok_error: not_implemented - real xAI endpoint not wired",
            })
            return data
# END stonecutter extension: grok provider
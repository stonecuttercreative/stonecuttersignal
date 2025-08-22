# BEGIN stonecutter extension
import os, json, asyncio
from typing import Dict, Any
from ._mock_util import mock_complete
from ..settings import settings

class OpenAIProvider:
    name = "openai"

    async def complete(self, prompt: str, **kw) -> Dict[str, Any]:
        if not settings.openai_api_key or not settings.enable_openai:
            return await mock_complete(self.name, prompt)
        # Minimal placeholder: call mock path for now to avoid SDK pinning.
        # Swap to real OpenAI client in a later step.
        return await mock_complete(self.name, prompt)
# END stonecutter extension
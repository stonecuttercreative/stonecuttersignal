# BEGIN stonecutter extension
from typing import Dict, Any
from ._mock_util import mock_complete
from ..settings import settings

class MistralProvider:
    name = "mistral"

    async def complete(self, prompt: str, **kw) -> Dict[str, Any]:
        if not settings.mistral_api_key or not settings.enable_mistral:
            return await mock_complete(self.name, prompt)
        return await mock_complete(self.name, prompt)
# END stonecutter extension
# BEGIN stonecutter extension
from typing import List
from .base import LLMProvider
from .openai_llm import OpenAIProvider
from .anthropic_llm import ClaudeProvider
from .gemini_llm import GeminiProvider
from .grok_llm import GrokProvider
from .perplexity_llm import PerplexityProvider
from .mistral_llm import MistralProvider
from ..settings import settings

def load_panel() -> List[LLMProvider]:
    """Return a list of enabled providers. If a provider lacks a key, it still loads but will mock."""
    panel: List[LLMProvider] = []
    if settings.enable_openai: panel.append(OpenAIProvider())
    if settings.enable_claude: panel.append(ClaudeProvider())
    if settings.enable_gemini: panel.append(GeminiProvider())
    if settings.enable_grok: panel.append(GrokProvider())
    if settings.enable_perplexity: panel.append(PerplexityProvider())
    if settings.enable_mistral: panel.append(MistralProvider())
    return panel
# END stonecutter extension
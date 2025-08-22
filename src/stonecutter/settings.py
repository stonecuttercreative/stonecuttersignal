# BEGIN stonecutter extension
from typing import Optional
try:
    from pydantic import BaseSettings, Field
except ImportError:
    from pydantic_settings import BaseSettings
    from pydantic import Field

class Settings(BaseSettings):
    mode: str = "realtime"
    max_concurrency: int = 8
    request_timeout_s: int = 20
    cache_enabled: bool = True

    # Feature flags
    feature_reddit_off: bool = True
    feature_tiktok_off: bool = True

    # Provider keys (optional)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_genai_key: Optional[str] = Field(default=None, env="GOOGLE_GENAI_API_KEY")
    xai_api_key: Optional[str] = Field(default=None, env="XAI_API_KEY")  # Grok
    perplexity_api_key: Optional[str] = Field(default=None, env="PERPLEXITY_API_KEY")
    mistral_api_key: Optional[str] = Field(default=None, env="MISTRAL_API_KEY")

    # BEGIN stonecutter extension: claude settings
    claude_model: str = "claude-3-5-sonnet-20240620"  # adjust if needed
    # END stonecutter extension

    # BEGIN stonecutter extension: gemini settings
    gemini_model: str = "gemini-1.5-pro"  # adjust if you prefer 'gemini-1.5-flash'
    # END stonecutter extension

    # Enable or disable each provider
    enable_openai: bool = True
    enable_claude: bool = True
    enable_gemini: bool = True
    enable_grok: bool = True
    enable_perplexity: bool = True
    enable_mistral: bool = True

    # Provider weights for arbitration
    weight_openai: float = 1.0
    weight_claude: float = 1.2
    weight_gemini: float = 1.1
    weight_grok: float = 1.0
    weight_perplexity: float = 1.1
    weight_mistral: float = 0.9

settings = Settings()
# END stonecutter extension
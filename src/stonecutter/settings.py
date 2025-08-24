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

# BEGIN stonecutter secure-keys
    # Provider keys (all optional; fallback to mock if missing)
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, env="ANTHROPIC_API_KEY")
    google_genai_key: str | None = Field(default=None, env="GOOGLE_GENAI_API_KEY")
    perplexity_api_key: str | None = Field(default=None, env="PERPLEXITY_API_KEY")
    xai_api_key: str | None = Field(default=None, env="XAI_API_KEY")

    openai_model: str = "gpt-4o-mini"
    claude_model: str = "claude-3-5-sonnet-20240620"
    gemini_model: str = "gemini-1.5-pro"
    perplexity_model: str = "llama-3.1-sonar-large-32k-online"
    grok_model: str = "grok-2-1212"

    enable_openai: bool = True
    enable_claude: bool = True
    enable_gemini: bool = True
    enable_perplexity: bool = True
    enable_grok: bool = True
    enable_mistral: bool = True
# END stonecutter secure-keys

    # Data layers
    newsapi_key: str | None = Field(default=None, env="NEWSAPI_KEY")
    enable_newsapi: bool = True
    enable_gdelt: bool = True
    evidence_max_items: int = 6

    # HTTP timeout for external calls
    http_timeout_s: int = 18


    # BEGIN stonecutter extension: persistence paths
    persistence_enabled: bool = True
    
    @property
    def db_path(self) -> str:
        """Get absolute path to SQLite database."""
        from pathlib import Path
        _ROOT = Path(__file__).resolve().parents[2]
        return str((_ROOT / "stonecutter.db").resolve())
    
    @property  
    def jsonl_path(self) -> str:
        """Get absolute path to JSONL log file."""
        from pathlib import Path
        _ROOT = Path(__file__).resolve().parents[2]
        return str((_ROOT / "data" / "run_logs.jsonl").resolve())
    # END stonecutter extension: persistence paths

    # Provider weights for arbitration
    weight_openai: float = 1.0
    weight_claude: float = 1.2
    weight_gemini: float = 1.1
    weight_grok: float = 1.0
    weight_perplexity: float = 1.1
    weight_mistral: float = 0.9

settings = Settings()
# END stonecutter extension
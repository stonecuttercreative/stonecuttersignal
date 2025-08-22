# Stonecutter Signal

AI-powered diagnostic analysis engine for campaign signal processing, leveraging multi-LLM integrations and comprehensive evidence gathering techniques.

## Features

- Multi-provider LLM arbitration system
- Real-time and historical evidence gathering
- Cultural archetype classification
- Interactive campaign brief analysis
- Comprehensive scoring framework

## Usage

Run the main analysis engine:
```bash
python stonecutter.py
```

Run validation checks:
```bash
python quick_check.py
```

### Using Claude (real API)
Set `ANTHROPIC_API_KEY` in Replit secrets. If unset, Claude falls back to a mock so runs never fail.
Check `compare_ab.py` to see per‑provider contributions and the arbitrated result.

### Using Gemini (real API)
Set `GOOGLE_GENAI_API_KEY` in Replit Secrets. If unset, Gemini falls back to a mock so runs never fail.
Default model: `gemini-1.5-pro` (change in settings if needed).

### Using Perplexity (real API)
Set `PERPLEXITY_API_KEY` in Replit Secrets. If unset, the provider falls back to a mock so runs never fail.
Default model: `llama-3.1-sonar-large-32k-online` (change in settings).

### Grok (xAI)
Set `XAI_API_KEY` in Replit Secrets to flip Grok live later.
Until then, provider returns deterministic mock responses with telemetry.
Model name defaults to `grok-2-1212` (change in settings).

### Testing Commands
```bash
python quick_check.py    # Validation tests
python compare_ab.py     # A/B provider comparison  
python test_providers.py # Provider system demo
```

## Architecture

The system uses a hybrid approach combining multiple LLM providers with deterministic orchestration logic for robust campaign analysis.
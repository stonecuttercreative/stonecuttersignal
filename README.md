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

## Dashboard

View recent analysis runs and performance metrics via the web dashboard:

```bash
python serve_dashboard.py
```

Visit http://localhost:8000 to see the dashboard with recent runs, confidence scores, and provider performance metrics.

### Seeding the Dashboard

Run sample analyses to populate the dashboard with test data:

```bash
python run_sample.py
```

This sends several example briefs through the full pipeline (providers → arbitration → scoring → persistence).
Open the dashboard at http://localhost:8000/ to view the populated results.

## Dashboard Visuals
- /metrics/timeseries → Line chart (confidence/consensus/diversity)
- /metrics/providers → Bar (latency), Doughnut (participation)
- /metrics/distribution → Histogram of scores
- /metrics/latest → Radar for most recent run
- /metrics/activity → Activity over last 30 days

# BEGIN stonecutter secure-keys
## Add API keys securely (Replit → Tools → Secrets)
Create these secrets (values = your raw keys; no quotes):
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GOOGLE_GENAI_API_KEY
- PERPLEXITY_API_KEY
- XAI_API_KEY   # Grok (stub until xAI endpoint is live)

Verify:
```bash
pip install -e .
python providers_health.py
# and open /health/providers
```
# END stonecutter secure-keys

# BEGIN stonecutter verify-keys
### Verify your API keys & live providers
1. In Replit → **Tools → Secrets**, add keys (values = raw keys, no quotes):
   - ANTHROPIC_API_KEY
   - GOOGLE_GENAI_API_KEY
   - PERPLEXITY_API_KEY
   - XAI_API_KEY   *(Grok; may be stub until wired)*
   - (optional) OPENAI_API_KEY
2. Run the verifier:
```bash
pip install -e .
python scripts/verify_keys.py
```
- The script checks env presence, runs a small ensemble, and prints each provider's expected vs actual mode with model + latency.
- Exit code 0 = all keyed providers responded LIVE. Exit code 2 = at least one keyed provider didn't respond LIVE.
# END stonecutter verify-keys

# BEGIN fix: openai-live
### Make OpenAI go LIVE
1) In Replit → Tools → Secrets add `OPENAI_API_KEY` (no quotes).
2) Verify:
```bash
pip install -e .
python scripts/diag_provider.py openai
python scripts/verify_keys.py
```
If diag_provider.py shows "model": null with an "openai_error": ..., fix the model name in settings.openai_model or ensure the OpenAI Python client is installed.
# END fix: openai-live

# BEGIN verify: providers
### Provider diagnostics
```bash
python scripts/diag_all.py
```
Expected: each of claude/gemini/perplexity/grok shows LIVE (model + latency) when keys are set, otherwise explicit error text.
# END verify: providers

# BEGIN composite: env+providers
### Quick env + SDK check
```bash
python scripts/check_env_sdks.py
```
Verify providers:
```bash
pip install -e .
python scripts/diag_all.py
```
- Each provider shows ✅ LIVE with model + latency if key and SDK are correct.
- If a provider fails, you'll see explicit *_error: text (missing key, model not found, HTTP error).
# END composite: env+providers

# BEGIN patch: perplexity+grok-live
### Live providers: Perplexity + Grok (xAI)
- **Perplexity** now tries small → large models and retries with two payload formats to avoid 400s on some tenants.
- **Grok/xAI** uses OpenAI-style `POST https://api.x.ai/v1/chat/completions` with `Authorization: Bearer $XAI_API_KEY`.
- Configure model defaults in `settings.py` (`perplexity_fallbacks`, `grok_fallbacks`).
- Verify:
```bash
pip install -e .
python scripts/diag_all.py
```
# END patch: perplexity+grok-live

# BEGIN patch: perplexity-safe-fallbacks
### Perplexity safe models
This project is pinned to commonly available Perplexity models:
- `llama-3.1-mini-4k-online` (default)
- `llama-3.1-sonar-small-128k-online` (fallback)

If your account supports additional models, update `perplexity_fallbacks` in `settings.py`.
# END patch: perplexity-safe-fallbacks

# BEGIN patch: perplexity-mini-fallbacks
### Perplexity Mini Models
Perplexity has been configured to use the most widely-available models:
- `llama-3.1-mini-4k-online` (default)
- `llama-3.1-mini-128k-online` (fallback)

If your account later gains access to Sonar models, update `perplexity_fallbacks` in `settings.py` accordingly.
# END patch: perplexity-mini-fallbacks

# BEGIN patch: perplexity-sonar-fallbacks
### Perplexity SONAR models
Perplexity is now configured to try SONAR models:
- `llama-3.1-sonar-small-128k-online` (default)
- `llama-3.1-sonar-large-32k-online` (fallback)

If your account exposes a different set, update `perplexity_fallbacks` in `settings.py` accordingly.
# END patch: perplexity-sonar-fallbacks

## Architecture

The system uses a hybrid approach combining multiple LLM providers with deterministic orchestration logic for robust campaign analysis.
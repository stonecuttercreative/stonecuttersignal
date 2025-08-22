# BEGIN stonecutter extension: compare script
import asyncio, json, sys, os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import directly from the main stonecutter.py file
sys.path.insert(0, os.path.dirname(__file__))
from stonecutter import run_signal_engine
try:
    from src.stonecutter.providers.registry import load_panel
    PANEL_AVAILABLE = True
except ImportError:
    PANEL_AVAILABLE = False

async def _panel(prompt: str):
    if not PANEL_AVAILABLE:
        return []
    panel = load_panel()
    outs = []
    for m in panel:
        r = await m.complete(prompt)
        r["_provider_name"] = getattr(m, "name", "unknown")
        outs.append(r)
    return outs

def build_prompt(brief: dict) -> str:
    """Build a prompt from brief components."""
    return f"""
Brand: {brief.get('brand', 'Unknown')}
Category: {brief.get('category', 'Unknown')}
Concept: {brief.get('concept', 'Unknown')}
Mode: {brief.get('mode', 'realtime')}
Audience: {brief.get('audience', 'N/A')}
Channels: {brief.get('channels', 'N/A')}

Analyze this campaign for cultural fit, clarity, emotional resonance, differentiation, conversation fit, and distribution fit.
""".strip()

def main():
    brief = {
        "brand":"Acme","category":"Finance","concept":"Clarity-first crypto education",
        "mode":"realtime","audience":"Adults 25-45 seeking stability","channels":"YouTube, CTV"
    }
    
    print("=== RUNNING ARBITRATED ANALYSIS ===")
    result = run_signal_engine(brief, interactive_mode=False)
    
    print("\n=== ARBITRATED RESULT ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Show raw provider contributions if available
    if PANEL_AVAILABLE:
        print("\n=== PROVIDER CONTRIBUTIONS ===")
        prompt = build_prompt(brief)
        raw = asyncio.run(_panel(prompt))
        print(f"Total providers called: {len(raw)}")
        for r in raw:
            name = r.get("_provider_name")
            scores = r.get("scores", {})
            telemetry = r.get("_telemetry", {})
            latency = telemetry.get("latency_ms", "N/A")
            model = telemetry.get("model", "mock")
            print(f"- {name} ({model}): cultural_fit={scores.get('cultural_fit')} clarity={scores.get('clarity')} conversation_fit={scores.get('conversation_fit')} latency={latency}ms")
    else:
        print("\n=== PROVIDER SYSTEM NOT AVAILABLE ===")
        print("Using OpenAI-only fallback mode")

if __name__ == "__main__":
    main()
# END stonecutter extension
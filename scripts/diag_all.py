# BEGIN verify: providers
import asyncio, json, sys
from typing import List, Dict, Any

async def run_once() -> Dict[str, Any]:
    import sys
    sys.path.append('.')
    from src.stonecutter.engine import run_signal
    
    payload = {"brand":"Diag","category":"Test",
               "concept":"Sanity check: short, neutral prompt for provider verification.",
               "channels":"YouTube"}
    return await run_signal(payload)

def pick(rowlist, name):
    return next((r for r in rowlist if (r.get("provider","").lower()==name)), None)

async def main():
    PROVIDERS = ["claude","gemini","perplexity","grok"]
    
    out = await run_once()
    rows: List[Dict[str,Any]] = out.get("providers") or []
    print("=== Provider diagnostics ===")
    ok_all = True
    for name in PROVIDERS:
        r = pick(rows, name)
        if not r:
            print(f"❌ {name}: not loaded into panel (check enable_* toggle / registry).")
            ok_all = False
            continue
        mode = "LIVE" if r.get("model") else "MOCK"
        err  = r.get("error")
        lat  = r.get("latency_ms")
        print(f"{'✅' if r.get('model') else '❌'} {name:<11} mode={mode} model={r.get('model')} latency_ms={lat} error={err}")
        if r.get("model") is None and err:
            ok_all = False
    # Exit non-zero if any provider with a key is not LIVE (verify_keys.py handles env presence)
    sys.exit(0 if ok_all else 2)

if __name__ == "__main__":
    asyncio.run(main())
# END verify: providers
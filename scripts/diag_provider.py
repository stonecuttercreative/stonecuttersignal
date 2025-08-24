# BEGIN fix: openai-live
import asyncio, time, sys, json

async def main():
    import sys
    sys.path.append('.')
    from src.stonecutter.engine import run_signal
    
    name = (sys.argv[1] if len(sys.argv) > 1 else "openai").lower()
    out = await run_signal({"brand":"Diag","category":"Test","concept":"Short sanity check."})
    rows = out.get("providers") or []
    row = next((r for r in rows if (r.get("provider","").lower()==name)), None)
    if not row:
        print(f"Provider '{name}' not found in run. Loaded providers: {[r.get('provider') for r in rows]}")
        sys.exit(2)
    print(json.dumps(row, ensure_ascii=False, indent=2))
    # exit non-zero if expected LIVE provider has no model
    live_expected = name in ("openai","claude","gemini","perplexity","grok")
    sys.exit(0 if (not live_expected or row.get("model")) else 3)

if __name__ == "__main__":
    asyncio.run(main())
# END fix: openai-live
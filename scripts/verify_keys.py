# BEGIN stonecutter verify-keys
import os, sys, time, json, asyncio
from typing import Dict, Any, List

# 1) Which providers are expected LIVE based on env?
ENV_MAP = {
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_GENAI_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "grok": "XAI_API_KEY",  # may be stubbed; still check presence
}

def env_present(name: str) -> bool:
    return bool(os.environ.get(name))

def expected_live() -> Dict[str, bool]:
    return {p: env_present(env) for p, env in ENV_MAP.items()}

async def run_quick_signal() -> Dict[str, Any]:
    # We import lazily so this script doesn't force app deps when unused.
    import sys
    sys.path.append('.')
    from src.stonecutter.engine import run_signal
    payload = {
        "brand": "HealthCheck",
        "category": "Sanity",
        "concept": "One-line sanity check about responsible crypto messaging.",
        "channels": "YouTube, CTV"
    }
    t0 = time.time()
    out = await run_signal(payload)
    out["_elapsed_ms"] = int((time.time() - t0) * 1000)
    return out

def summarize_providers(run_out: Dict[str, Any]) -> List[Dict[str, Any]]:
    provs: List[Dict[str, Any]] = run_out.get("providers") or []
    # Normalize common fields defensively
    rows = []
    for p in provs:
        rows.append({
            "provider": p.get("provider") or p.get("name") or "?",
            "model": p.get("model"),
            "latency_ms": p.get("latency_ms"),
            "error": p.get("error"),
            "mode": ("LIVE" if p.get("model") else "MOCK")
        })
    return rows

def print_report(env_expect: Dict[str,bool], rows: List[Dict[str,Any]], elapsed_ms: int):
    print("\n=== Provider Key Verification ===")
    print(f"Ensemble elapsed: {elapsed_ms} ms")
    ok_all = True
    for name, need_live in env_expect.items():
        # find row for provider (by case-insensitive match)
        r = next((x for x in rows if (x["provider"] or "").lower() == name.lower()), None)
        state = "MISSING"
        if r:
            state = r["mode"]
        live_ok = (not need_live) or (state == "LIVE")
        ok_all &= live_ok
        badge = "✅" if live_ok else "❌"
        extra = ""
        if r:
            extra = f"  model={r['model']}, latency_ms={r['latency_ms']}, error={r['error']}"
        print(f"{badge} {name:<11} expected={'LIVE' if need_live else 'MOCK'}  got={state}{extra}")
    return ok_all

async def main():
    env_expect = expected_live()

    # Optional: try the web health endpoint if the app server is up
    # (non-fatal if it fails—this script is primarily engine-based)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get("http://localhost:8000/health/providers")
            if r.status_code == 200:
                hp = r.json()
                print("\n/health/providers:", json.dumps(hp, ensure_ascii=False))
    except Exception:
        pass

    # Run a tiny ensemble and examine provider telemetry
    out = await run_quick_signal()
    rows = summarize_providers(out)
    ok = print_report(env_expect, rows, out.get("_elapsed_ms", -1))

    # Exit non-zero if any keyed provider failed to show LIVE
    sys.exit(0 if ok else 2)

if __name__ == "__main__":
    asyncio.run(main())
# END stonecutter verify-keys
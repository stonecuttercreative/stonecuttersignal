# BEGIN stonecutter secure-keys
import asyncio, os, time
from src.stonecutter.engine import run_signal

def ok(n): return "✅" if os.environ.get(n) else "⚠️"
def show_env():
    print("Keys:", f"OpenAI:{ok('OPENAI_API_KEY')}",
          f"Claude:{ok('ANTHROPIC_API_KEY')}",
          f"Gemini:{ok('GOOGLE_GENAI_API_KEY')}",
          f"Perplexity:{ok('PERPLEXITY_API_KEY')}",
          f"Grok:{ok('XAI_API_KEY')}", sep="  ")

async def quick():
    payload={"brand":"HealthCheck","category":"Sanity",
             "concept":"One-line sanity check about responsible crypto messaging."}
    t0=time.time(); out=await run_signal(payload); dt=int((time.time()-t0)*1000)
    print(f"\nArbitration completed in {dt} ms")
    for p in (out.get("providers") or []):
        live = "LIVE" if p.get("model") else "MOCK"
        print(f" - {p.get('provider')}: {live} (model={p.get('model')}, latency_ms={p.get('latency_ms')})")
    sig=(out.get('meta') or {}).get('signal_scores',{})
    print("Signal:", {k:sig.get(k) for k in ('confidence','consensus','diversity')})

if __name__=="__main__":
    show_env()
    asyncio.run(quick())
# END stonecutter secure-keys
# BEGIN patch: list-perplexity-models
import os, sys, json, textwrap
import httpx

API_URL = "https://api.perplexity.ai/models"

def main():
    key = os.getenv("PERPLEXITY_API_KEY")
    if not key:
        print("❌ PERPLEXITY_API_KEY is not set (Replit → Tools → Secrets).")
        sys.exit(2)

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(API_URL, headers={"Authorization": f"Bearer {key}"})
        if r.status_code != 200:
            print(f"❌ HTTP {r.status_code}: {r.text[:300]}")
            sys.exit(3)
        data = r.json()
    except Exception as e:
        print(f"❌ Request failed: {type(e).__name__}: {e}")
        sys.exit(4)

    # Perplexity responds with a list or an object containing 'data'
    models = data.get("data", data)
    if not isinstance(models, list) or not models:
        print("⚠️ No models returned for this key.")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        sys.exit(0)

    # Normalize possible shapes
    rows = []
    for m in models:
        mid = m.get("id") or m.get("model") or m.get("name") or "?"
        family = m.get("family") or m.get("type") or ""
        ctx = m.get("context_length") or m.get("context") or ""
        desc = m.get("description") or ""
        rows.append((mid, str(family), str(ctx), desc))

    # Pretty print
    print("\n✅ Perplexity models available to this API key:\n")
    print(f"{'model_id':40}  {'family':18}  {'context':8}  description")
    print("-"*100)
    for mid, fam, ctx, desc in rows:
        d = textwrap.shorten(desc, width=60, placeholder="…")
        print(f"{mid:40}  {fam:18}  {ctx:8}  {d}")

    # Also print a JSON list you can copy into settings.py
    ids = [r[0] for r in rows if r[0] and r[0] != "?"]
    print("\nCopy-paste for settings.py (perplexity_fallbacks):")
    print(json.dumps(ids, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
# END patch: list-perplexity-models
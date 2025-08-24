# BEGIN composite: env+providers
import os, importlib

print("=== Env Vars ===")
for name in ["ANTHROPIC_API_KEY","GOOGLE_GENAI_API_KEY","GOOGLE_API_KEY",
             "PERPLEXITY_API_KEY","XAI_API_KEY","OPENAI_API_KEY"]:
    print(f"{name:<22}", "✅" if os.getenv(name) else "❌")

print("\n=== SDK Modules ===")
for mod in ["anthropic","google.generativeai","httpx","openai"]:
    try:
        importlib.import_module(mod)
        print(f"{mod:<22} ✅")
    except Exception as e:
        print(f"{mod:<22} ❌ ({e.__class__.__name__}: {e})")
# END composite: env+providers
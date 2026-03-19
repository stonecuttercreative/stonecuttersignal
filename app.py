"""
Stonecutter Signal — chat interface
Usage:  python3 app.py
        Opens http://localhost:8000 automatically.
"""
import sys, os, json, asyncio, re, time, threading, webbrowser
from pathlib import Path

# ── Path setup ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import anthropic
import uvicorn

from stonecutter.settings import settings

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI()
_HTML_PATH = ROOT / "static" / "index.html"
_STATIC_DIR = ROOT / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/")
async def index():
    return HTMLResponse(_HTML_PATH.read_text())


# ── Brief extraction (fast haiku call) ───────────────────────────────────────
_EXTRACT_SYS = """\
You are a creative strategist gathering a campaign brief. Reply with ONLY valid JSON — no prose, no markdown.

A brief is READY when you have real, specific values (not "Unknown") for ALL THREE:
  • brand    — the company or product name
  • concept  — a specific campaign idea, not just a vague goal (e.g. "Serena Williams front a women's empowerment film" not just "empowerment campaign")
  • audience — who this is actually for, with some specificity (e.g. "Gen Z women 18-24" not just "everyone")

Category and channels can always be inferred — never ask about them.

When all three are clear, respond:
{"ready": true, "brief": {"brand": "...", "category": "...", "concept": "...", "audience": "...", "channels": "..."}}

When something critical is missing, ask exactly ONE short, conversational question — pick the highest-priority gap:
  1. concept unclear or too vague  → ask what the core campaign idea or message is
  2. brand not mentioned            → ask what brand or company this is for
  3. audience vague or missing      → ask who the specific target audience is

{"ready": false, "question": "..."}

Never ask about category or channels. Never ask two questions at once.
"""

_EXTRACT_MODELS = ["claude-haiku-4-5-20251001", "claude-3-5-sonnet-20241022"]


async def extract_brief(history: list[dict]) -> dict:
    user_turns = sum(1 for m in history if m["role"] == "user")
    # After 3 exchanges, force the analysis with whatever we have
    force = "\n\nThe user has now replied 3+ times. You MUST return ready:true now — fill any remaining gaps with your best inference." if user_turns >= 3 else ""

    hist_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    for model in _EXTRACT_MODELS:
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=280,
                temperature=0,
                system=_EXTRACT_SYS + force,
                messages=[{"role": "user", "content": hist_text}],
            )
            raw = resp.content[0].text.strip()
            # Strip any stray markdown fences
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
            if m:
                raw = m.group(1).strip()
            return json.loads(raw)
        except anthropic.NotFoundError:
            continue
        except Exception:
            break

    # Hard fallback
    return {"ready": False, "question": "What brand is this campaign for?"}


# ── Progress helper ───────────────────────────────────────────────────────────
async def _run_with_progress(brief: dict, send) -> dict:
    """Run engine with timed progress messages."""
    from stonecutter.engine import run_signal

    engine_task = asyncio.create_task(run_signal(brief))

    steps_init = [
        {"id": "kb",     "label": "Searching historical campaigns",          "done": False, "active": True},
        {"id": "signal", "label": "Gathering live Reddit signal",            "done": False, "active": False},
        {"id": "claude", "label": "Running analysis",                        "done": False, "active": False},
    ]
    await send("progress", steps=steps_init)

    # ~0.6s: KB done, evidence starting
    await asyncio.sleep(0.6)
    if not engine_task.done():
        await send("progress", steps=[
            {"id": "kb",     "label": "Historical campaigns searched",       "done": True,  "active": False},
            {"id": "signal", "label": "Gathering live Reddit signal",        "done": False, "active": True},
            {"id": "claude", "label": "Running analysis",                    "done": False, "active": False},
        ])

    # ~5s: evidence done, Claude starting
    await asyncio.sleep(4.5)
    if not engine_task.done():
        await send("progress", steps=[
            {"id": "kb",     "label": "Historical campaigns searched",       "done": True, "active": False},
            {"id": "signal", "label": "Live signal gathered",               "done": True, "active": False},
            {"id": "claude", "label": "Running analysis — usually 20–30 s", "done": False, "active": True},
        ])

    result = await engine_task

    # Annotate signal step with subreddits once we have result
    subs = sorted({
        (e.get("source") or "").split(" ")[0]
        for e in result.get("evidence", [])
        if e.get("provider") == "reddit"
    })
    sig_label = f"Live signal — {', '.join(subs[:4])}" if subs else "Live signal gathered"

    await send("progress", steps=[
        {"id": "kb",     "label": "Historical campaigns searched", "done": True, "active": False},
        {"id": "signal", "label": sig_label,                       "done": True, "active": False},
        {"id": "claude", "label": "Analysis complete",             "done": True, "active": False},
    ])
    await asyncio.sleep(0.25)
    return result


# ── WebSocket conversation ────────────────────────────────────────────────────
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    history: list[dict] = []

    async def send(msg_type: str, **kwargs):
        await ws.send_json({"type": msg_type, **kwargs})

    await send(
        "message",
        content="Describe your campaign idea. Rough is fine — brand, concept, "
                "audience, whatever you have. I'll ask if I need anything else.",
    )

    try:
        while True:
            data = await ws.receive_json()

            if data.get("type") == "new_conversation":
                history.clear()
                await send(
                    "message",
                    content="Ready. Describe your next campaign idea.",
                )
                continue

            user_msg = (data.get("content") or "").strip()
            if not user_msg:
                continue

            history.append({"role": "user", "content": user_msg})

            # Show typing indicator while extracting brief
            await send("typing")

            try:
                extraction = await extract_brief(history)
            except Exception:
                await send(
                    "message",
                    content="Got it. What brand is this campaign for?",
                )
                history.append({"role": "assistant", "content": "What brand is this campaign for?"})
                continue

            if not extraction.get("ready"):
                question = extraction.get("question", "What brand is this campaign for?")
                history.append({"role": "assistant", "content": question})
                await send("message", content=question)
                continue

            # We have a brief — confirm and run
            brief = extraction["brief"]
            brand = brief.get("brand") or "Unknown"
            category = brief.get("category") or ""
            confirm = (
                f"Running analysis for **{brand}**"
                + (f" — {category}" if category and category != "Unknown" else "")
                + ". Gathering live signal and searching historical campaigns."
            )
            history.append({"role": "assistant", "content": confirm})
            await send("message", content=confirm)

            try:
                result = await _run_with_progress(brief, send)
                await send("analysis", data=result)
            except Exception as e:
                await send(
                    "error",
                    content=f"Analysis failed: {e}. Check that your API key is set in .env.",
                )

    except WebSocketDisconnect:
        pass


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _port = int(os.environ.get("PORT", 8000))
    _prod = bool(os.environ.get("PORT"))
    _host = "0.0.0.0" if _prod else "127.0.0.1"

    if not _prod:
        def _open():
            time.sleep(1.8)
            webbrowser.open(f"http://localhost:{_port}")
        threading.Thread(target=_open, daemon=True).start()

    print()
    print("  ◈  STONECUTTER SIGNAL")
    print("  ─────────────────────────────────────")
    print(f"  http://{'0.0.0.0' if _prod else 'localhost'}:{_port}")
    print()

    uvicorn.run(app, host=_host, port=_port, log_level="warning")

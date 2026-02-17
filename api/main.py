"""FastAPI backend for ESPN Fantasy Basketball bot."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path so we can import main (bot)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import FantasyBot, DEFAULT_CONTEXT_PATH

app = FastAPI(title="Fantasy Bot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_bot() -> FantasyBot:
    """Create bot instance using env / context from project root."""
    return FantasyBot(context_path=ROOT / "context.json")


class ExecuteBody(BaseModel):
    confirm: bool = False
    generate_new: bool = False


@app.get("/analyze")
def analyze():
    """Return structured suggestions (IR, lineup, streaming). No side effects."""
    try:
        bot = get_bot()
        suggestions = bot.get_suggestions()
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute")
def execute(body: ExecuteBody):
    """Execute changes (confirm=True) or return new suggestions (generate_new=True)."""
    try:
        bot = get_bot()
        if body.confirm:
            actions = bot.run_daily_cycle(dry_run=False, api_confirm=True)
            return {"executed": True, "actions": actions}
        if body.generate_new:
            suggestions = bot.get_suggestions()
            return {"executed": False, "suggestions": suggestions}
        return {"executed": False, "actions": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}

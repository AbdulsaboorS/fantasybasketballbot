"""FastAPI backend for ESPN Fantasy Basketball bot."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path so we can import main (bot)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import secrets

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import FantasyBot, DEFAULT_CONTEXT_PATH

app = FastAPI(title="Fantasy Bot API", version="0.1.0")

_API_PASSWORD = os.getenv("API_PASSWORD")
_valid_tokens: set[str] = set()


def _require_auth(authorization: str | None = Header(default=None)) -> None:
    """If API_PASSWORD is set, require a valid bearer token."""
    if not _API_PASSWORD:
        return  # no password configured — open access (local dev)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[len("Bearer "):].strip()
    if token not in _valid_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_bot() -> FantasyBot:
    """Create bot instance using env / context from project root."""
    return FantasyBot(context_path=ROOT / "context.json")


class AuthBody(BaseModel):
    password: str


class ExecuteBody(BaseModel):
    confirm: bool = False
    generate_new: bool = False


class ExecuteLineupBody(BaseModel):
    starter_player_id: int
    replacement_player_id: int
    starter_slot: str = "BE"


@app.post("/auth")
def auth(body: AuthBody):
    """Exchange a password for a session token.

    Returns {"token": "<hex>", "authenticated": true} on success.
    If API_PASSWORD is not set, returns {"token": null, "authenticated": true}
    (open access — local dev).
    """
    if not _API_PASSWORD:
        return {"token": None, "authenticated": True}
    if body.password != _API_PASSWORD:
        raise HTTPException(status_code=401, detail="Incorrect password")
    token = secrets.token_hex(32)
    _valid_tokens.add(token)
    return {"token": token, "authenticated": True}


@app.get("/analyze")
def analyze():
    """Return structured suggestions (IR, lineup, streaming) plus team metadata.

    Response shape:
    {
        "ir": string[],
        "lineup": string[],
        "streaming": string[],
        "team": {"name": string, "record": string}
    }
    """
    try:
        bot = get_bot()
        suggestions = bot.get_suggestions()
        team_name = getattr(bot.team, "team_name", "") or ""
        record = bot.context.get("season", {}).get("current_record", "")
        return {**suggestions, "team": {"name": team_name, "record": record}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute")
def execute(body: ExecuteBody, _auth: None = Depends(_require_auth)):
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


@app.get("/lineup-status")
def lineup_status():
    """Return game-day lineup status: urgent swaps and questionable starters.

    Response shape:
    {
        "urgent_swaps": [
            {
                "starter_name": string,
                "starter_status": string,
                "starter_ppg": float,
                "replacement_name": string,
                "replacement_ppg": float,
                "starter_player_id": int,
                "replacement_player_id": int,
                "starter_slot": string
            }
        ],
        "questionable": [
            {"name": string, "status": string, "ppg": float}
        ]
    }
    """
    try:
        bot = get_bot()
        return bot.check_lineup_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute-lineup")
def execute_lineup(body: ExecuteLineupBody, _auth: None = Depends(_require_auth)):
    """Execute a single lineup swap (bench injured starter, promote replacement).

    Response: {"success": bool, "message": string}
    """
    try:
        bot = get_bot()
        message = bot.execute_lineup_swap(
            starter_player_id=body.starter_player_id,
            replacement_player_id=body.replacement_player_id,
            starter_slot=body.starter_slot,
        )
        return {"success": "failed" not in message.lower(), "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/last-run")
def last_run():
    """Return the most recent bot run summary from context.json tracking section."""
    try:
        bot = get_bot()
        tracking = bot.context.get("tracking", {})
        return {
            "last_run_utc": tracking.get("last_run_utc"),
            "moves_made_today": tracking.get("moves_made_today", []),
            "weekly_transactions_used": tracking.get("weekly_transactions_used", 0),
            "plan_for_tomorrow": tracking.get("plan_for_tomorrow", ""),
            "current_record": bot.context.get("season", {}).get("current_record", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}

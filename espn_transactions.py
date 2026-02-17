"""
ESPN Fantasy Basketball add/drop transactions via direct API POST.

The espn-api library does not support write operations (add/drop) for basketball.
This module sends a single add/drop transaction to ESPN's transaction endpoint
using credentials and (optionally) a URL + body you capture from the browser.

Setup:
  1. Capture one add/drop request from ESPN (see CAPTURE_TRANSACTION.md).
  2. Set ESPN_TRANSACTION_URL to the request URL (or leave unset to use default).
  3. Set ESPN_TRANSACTION_BODY or ESPN_TRANSACTION_BODY_FILE to the JSON body,
     with placeholders {league_id}, {team_id}, {year}, {drop_player_id}, {add_player_id}
     replaced at runtime (or use the format your captured request uses).
"""

from __future__ import annotations

import json
import os
from pathlib import Path


# Default write API base (captured from browser: ESPN POST goes to lm-api-writes).
_DEFAULT_BASE = "https://lm-api-writes.fantasy.espn.com"
_FBA_PATH = "/apis/v3/games/fba/seasons/{year}/segments/0/leagues/{league_id}/transactions"


def _get_cookies(swid: str, espn_s2: str) -> dict[str, str]:
    """Build cookie dict for ESPN requests."""
    return {"SWID": swid, "espn_s2": espn_s2}


def _get_transaction_url(league_id: int, year: int) -> str:
    """Transaction POST URL from env or default."""
    url = os.getenv("ESPN_TRANSACTION_URL", "").strip()
    if url:
        return url
    base = os.getenv("ESPN_TRANSACTION_BASE", _DEFAULT_BASE).strip() or _DEFAULT_BASE
    path = _FBA_PATH.format(league_id=league_id, year=year)
    return base.rstrip("/") + path


def _get_transaction_body(
    league_id: int,
    team_id: int,
    year: int,
    drop_player_id: int,
    add_player_id: int,
) -> dict:
    """
    Build POST JSON body from env (file or string) with placeholders,
    or return a minimal default body for testing.
    """
    body_file = os.getenv("ESPN_TRANSACTION_BODY_FILE", "").strip()
    if body_file and Path(body_file).exists():
        raw = Path(body_file).read_text(encoding="utf-8")
    else:
        raw = os.getenv("ESPN_TRANSACTION_BODY", "").strip()

    if raw:
        # Replace placeholders (case-insensitive)
        replacements = {
            "{league_id}": str(league_id),
            "{team_id}": str(team_id),
            "{year}": str(year),
            "{drop_player_id}": str(drop_player_id),
            "{add_player_id}": str(add_player_id),
        }
        for placeholder, value in replacements.items():
            raw = raw.replace(placeholder, value)
        return json.loads(raw)

    # Default body shape (may not match ESPN's actual API; user should capture real one).
    # Many ESPN transaction APIs expect something like this; adjust after capture.
    return {
        "type": "ROSTER",
        "memberId": str(team_id),
        "executionType": "EXECUTE",
        "items": [
            {"playerId": add_player_id, "type": "ADD", "fromSlotId": 0},
            {"playerId": drop_player_id, "type": "DROP", "fromSlotId": 0},
        ],
    }


def add_drop(
    league_id: int,
    team_id: int,
    year: int,
    swid: str,
    espn_s2: str,
    drop_player_id: int,
    add_player_id: int,
) -> None:
    """
    Execute one add/drop transaction: drop drop_player_id, add add_player_id.

    Uses ESPN_TRANSACTION_URL (or default) and ESPN_TRANSACTION_BODY / ESPN_TRANSACTION_BODY_FILE
    if set. Raises on HTTP error or if ESPN returns an error in the JSON response.
    """
    import requests

    url = _get_transaction_url(league_id, year)
    body = _get_transaction_body(
        league_id=league_id,
        team_id=team_id,
        year=year,
        drop_player_id=drop_player_id,
        add_player_id=add_player_id,
    )
    cookies = _get_cookies(swid, espn_s2)
    headers = {"Content-Type": "application/json"}

    resp = requests.post(url, json=body, cookies=cookies, headers=headers, timeout=30)

    if resp.status_code >= 400:
        raise RuntimeError(
            f"ESPN transaction failed: HTTP {resp.status_code} — {resp.text[:500]}"
        )

    data = resp.json() if resp.text else {}
    # Some APIs return { "error": "..." } or { "messages": ["..."] } on failure
    if isinstance(data, dict):
        if data.get("error"):
            raise RuntimeError(f"ESPN transaction error: {data.get('error')}")
        for key in ("messages", "message"):
            msgs = data.get(key)
            if isinstance(msgs, list) and msgs and isinstance(msgs[0], dict):
                msg = msgs[0].get("message") or msgs[0].get("text") or str(msgs[0])
                if "error" in msg.lower() or "invalid" in msg.lower():
                    raise RuntimeError(f"ESPN transaction error: {msg}")
            elif isinstance(msgs, str) and ("error" in msgs.lower() or "invalid" in msgs.lower()):
                raise RuntimeError(f"ESPN transaction error: {msgs}")

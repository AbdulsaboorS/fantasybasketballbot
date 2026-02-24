"""
ESPN Fantasy Basketball add/drop transactions via direct API POST.

The espn-api library does not support write operations (add/drop) for basketball.
This module sends a single add/drop transaction to ESPN's transaction endpoint
using credentials and (optionally) a URL + body you capture from the browser.

Setup:
  1. Set SWID, ESPN_S2, LEAGUE_ID, TEAM_ID in your .env file.
  2. Optionally set ESPN_TRANSACTION_BODY or ESPN_TRANSACTION_BODY_FILE to override
     the default body, with placeholders {league_id}, {team_id}, {year},
     {drop_player_id}, {add_player_id}, {scoring_period_id}.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


# Confirmed write endpoint from browser capture.
_DEFAULT_BASE = "https://lm-api-writes.fantasy.espn.com"
_FBA_PATH = "/apis/v3/games/fba/seasons/{year}/segments/0/leagues/{league_id}/transactions/"

# Headers required by ESPN's transaction API (confirmed from browser capture).
_HEADERS = {
    "Content-Type": "application/json",
    "x-fantasy-platform": "espn-fantasy-web",
    "x-fantasy-source": "kona",
}


def _get_cookies(swid: str, espn_s2: str) -> dict[str, str]:
    return {"SWID": swid, "espn_s2": espn_s2}


def _get_transaction_url(league_id: int, year: int) -> str:
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
    scoring_period_id: int,
) -> dict:
    """
    Build POST JSON body from env (file or string) with placeholders,
    or return the correct ESPN FREEAGENT add/drop body format.
    """
    body_file = os.getenv("ESPN_TRANSACTION_BODY_FILE", "").strip()
    if body_file and Path(body_file).exists():
        raw = Path(body_file).read_text(encoding="utf-8")
    else:
        raw = os.getenv("ESPN_TRANSACTION_BODY", "").strip()

    if raw:
        replacements = {
            "{league_id}": str(league_id),
            "{team_id}": str(team_id),
            "{year}": str(year),
            "{drop_player_id}": str(drop_player_id),
            "{add_player_id}": str(add_player_id),
            "{scoring_period_id}": str(scoring_period_id),
        }
        for placeholder, value in replacements.items():
            raw = raw.replace(placeholder, value)
        return json.loads(raw)

    # Confirmed body format from browser capture (Feb 2026).
    # type "FREEAGENT" = add from free agents; items list ADD then DROP.
    return {
        "isLeagueManager": False,
        "teamId": team_id,
        "type": "FREEAGENT",
        "scoringPeriodId": scoring_period_id,
        "executionType": "EXECUTE",
        "items": [
            {"playerId": add_player_id, "type": "ADD", "toTeamId": team_id},
            {"playerId": drop_player_id, "type": "DROP", "fromTeamId": team_id},
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
    scoring_period_id: int = 0,
) -> None:
    """
    Execute one add/drop transaction: drop drop_player_id, add add_player_id.

    scoring_period_id should be the current ESPN scoring period (fetched from
    league.scoringPeriodId). Raises on HTTP error or ESPN error in response.
    """
    import requests

    url = _get_transaction_url(league_id, year)
    body = _get_transaction_body(
        league_id=league_id,
        team_id=team_id,
        year=year,
        drop_player_id=drop_player_id,
        add_player_id=add_player_id,
        scoring_period_id=scoring_period_id,
    )
    cookies = _get_cookies(swid, espn_s2)

    resp = requests.post(url, json=body, cookies=cookies, headers=_HEADERS, timeout=30)

    if resp.status_code >= 400:
        raise RuntimeError(
            f"ESPN transaction failed: HTTP {resp.status_code} — {resp.text[:500]}"
        )

    data = resp.json() if resp.text else {}
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

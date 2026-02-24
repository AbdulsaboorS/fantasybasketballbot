"""
ESPN Fantasy Basketball lineup swap via direct API POST.

The espn-api library has no write methods for basketball lineup changes.
This module sends a lineup-swap transaction to ESPN's transaction endpoint
using the same credentials and pattern as espn_transactions.py.

Setup:
  1. Set SWID, ESPN_S2, LEAGUE_ID, TEAM_ID in your .env file.
  2. Optionally set ESPN_LINEUP_URL to override the default endpoint.
  3. Optionally set ESPN_LINEUP_BODY or ESPN_LINEUP_BODY_FILE to override
     the default body, with placeholders {league_id}, {team_id}, {year},
     {scoring_period_id}, {starter_player_id}, {replacement_player_id},
     {starter_slot_id}, {bench_slot_id}.

Standard NBA ESPN slot IDs (defaults — confirm from your browser capture,
see CAPTURE_LINEUP.md):
  0  = PG
  1  = SG
  2  = SF
  3  = PF
  4  = C
  5  = G  (Guard flex)
  6  = F  (Forward flex)
  8  = UTIL
  9  = BE (Bench)
  12 = IR / IL
"""

from __future__ import annotations

import json
import os
from pathlib import Path


# Same confirmed write host as add/drop transactions.
_DEFAULT_BASE = "https://lm-api-writes.fantasy.espn.com"
_FBA_PATH = "/apis/v3/games/fba/seasons/{year}/segments/0/leagues/{league_id}/transactions/"

# Same headers required for all ESPN write API calls (confirmed from browser capture).
_HEADERS = {
    "Content-Type": "application/json",
    "x-fantasy-platform": "espn-fantasy-web",
    "x-fantasy-source": "kona",
}

# Standard ESPN NBA fantasy slot IDs. May vary by league configuration.
# Capture a real lineup-change request (see CAPTURE_LINEUP.md) to confirm.
SLOT_IDS: dict[str, int] = {
    "PG":   0,
    "SG":   1,
    "SF":   2,
    "PF":   3,
    "C":    4,
    "G":    5,   # Guard flex
    "F":    6,   # Forward flex
    "UTIL": 8,
    "BE":   9,
    "BN":   9,   # alias for bench
    "IR":   12,
    "IL":   12,  # alias for IR
}


def get_slot_id(slot_name: str) -> int:
    """Convert a slot position string to its ESPN numeric slot ID.

    Defaults to 9 (bench) if the slot name is not in the standard mapping.
    """
    return SLOT_IDS.get(str(slot_name).upper(), 9)


def _get_cookies(swid: str, espn_s2: str) -> dict[str, str]:
    return {"SWID": swid, "espn_s2": espn_s2}


def _get_lineup_url(league_id: int, year: int) -> str:
    """Return the ESPN lineup-change POST endpoint URL.

    Override with ESPN_LINEUP_URL env var if the default does not work.
    """
    url = os.getenv("ESPN_LINEUP_URL", "").strip()
    if url:
        return url
    base = os.getenv("ESPN_LINEUP_BASE", _DEFAULT_BASE).strip() or _DEFAULT_BASE
    path = _FBA_PATH.format(league_id=league_id, year=year)
    return base.rstrip("/") + path


def _get_lineup_body(
    league_id: int,
    team_id: int,
    year: int,
    scoring_period_id: int,
    starter_player_id: int,
    replacement_player_id: int,
    starter_slot_id: int,
    bench_slot_id: int,
    swid: str = "",
) -> dict:
    """Build POST JSON body for a lineup swap.

    Body format confirmed from browser DevTools capture (200 OK response).
    Key findings:
      - Outer "type" must be "ROSTER" (not "LINEUP")
      - Item slot fields are "fromLineupSlotId"/"toLineupSlotId"
      - "memberId" (= SWID cookie value) is required in the body

    Uses ESPN_LINEUP_BODY_FILE or ESPN_LINEUP_BODY env var with placeholders
    if set. Otherwise returns the confirmed default body.

    Placeholders supported in custom body:
      {league_id}, {team_id}, {year}, {scoring_period_id},
      {starter_player_id}, {replacement_player_id},
      {starter_slot_id}, {bench_slot_id}, {member_id}
    """
    body_file = os.getenv("ESPN_LINEUP_BODY_FILE", "").strip()
    if body_file and Path(body_file).exists():
        raw = Path(body_file).read_text(encoding="utf-8")
    else:
        raw = os.getenv("ESPN_LINEUP_BODY", "").strip()

    if raw:
        replacements = {
            "{league_id}": str(league_id),
            "{team_id}": str(team_id),
            "{year}": str(year),
            "{scoring_period_id}": str(scoring_period_id),
            "{starter_player_id}": str(starter_player_id),
            "{replacement_player_id}": str(replacement_player_id),
            "{starter_slot_id}": str(starter_slot_id),
            "{bench_slot_id}": str(bench_slot_id),
            "{member_id}": swid,
        }
        for placeholder, value in replacements.items():
            raw = raw.replace(placeholder, value)
        return json.loads(raw)

    # Confirmed body format from browser capture (HTTP 200, status=EXECUTED).
    # Outer type is "ROSTER"; item slot fields are fromLineupSlotId/toLineupSlotId.
    return {
        "isLeagueManager": False,
        "teamId": team_id,
        "type": "ROSTER",
        "scoringPeriodId": scoring_period_id,
        "executionType": "EXECUTE",
        "memberId": swid,
        "items": [
            {
                "playerId": replacement_player_id,
                "type": "LINEUP",
                "fromLineupSlotId": bench_slot_id,
                "toLineupSlotId": starter_slot_id,
                "fromTeamId": 0,
                "toTeamId": 0,
            },
            {
                "playerId": starter_player_id,
                "type": "LINEUP",
                "fromLineupSlotId": starter_slot_id,
                "toLineupSlotId": bench_slot_id,
                "fromTeamId": 0,
                "toTeamId": 0,
            },
        ],
    }


def lineup_swap(
    league_id: int,
    team_id: int,
    year: int,
    swid: str,
    espn_s2: str,
    starter_player_id: int,
    replacement_player_id: int,
    starter_slot_id: int,
    bench_slot_id: int = 9,
    scoring_period_id: int = 0,
) -> None:
    """Execute one lineup swap: bench the injured starter, promote the replacement.

    Args:
        starter_player_id: ESPN player ID of the player to move to bench (OUT/DTD).
        replacement_player_id: ESPN player ID of the bench player to promote.
        starter_slot_id: Numeric ESPN slot ID of the starting position (e.g. 0 for PG).
        bench_slot_id: Numeric ESPN slot ID of the bench slot (default 9 = BE).
        scoring_period_id: Current ESPN scoring period (from league.scoringPeriodId).

    Raises:
        RuntimeError: On HTTP error or ESPN error in response body.

    Note:
        If ESPN rejects the default body, capture a real lineup-change request
        from your browser and set ESPN_LINEUP_BODY or ESPN_LINEUP_BODY_FILE.
        See CAPTURE_LINEUP.md for step-by-step instructions.
    """
    import requests

    url = _get_lineup_url(league_id, year)
    body = _get_lineup_body(
        league_id=league_id,
        team_id=team_id,
        year=year,
        scoring_period_id=scoring_period_id,
        starter_player_id=starter_player_id,
        replacement_player_id=replacement_player_id,
        starter_slot_id=starter_slot_id,
        bench_slot_id=bench_slot_id,
        swid=swid,
    )
    cookies = _get_cookies(swid, espn_s2)

    print(f"[lineup_swap] POST {url}")
    print(f"[lineup_swap] body: {json.dumps(body, indent=2)}")
    resp = requests.post(url, json=body, cookies=cookies, headers=_HEADERS, timeout=30)
    print(f"[lineup_swap] ESPN response: HTTP {resp.status_code}")
    print(f"[lineup_swap] ESPN body: {resp.text}")

    if resp.status_code >= 400:
        raise RuntimeError(
            f"ESPN lineup swap failed: HTTP {resp.status_code} — {resp.text[:500]}"
        )

    data = resp.json() if resp.text else {}
    if isinstance(data, dict):
        if data.get("error"):
            raise RuntimeError(f"ESPN lineup error: {data.get('error')}")
        for key in ("messages", "message"):
            msgs = data.get(key)
            if isinstance(msgs, list) and msgs and isinstance(msgs[0], dict):
                msg = msgs[0].get("message") or msgs[0].get("text") or str(msgs[0])
                if "error" in msg.lower() or "invalid" in msg.lower():
                    raise RuntimeError(f"ESPN lineup error: {msg}")
            elif isinstance(msgs, str) and ("error" in msgs.lower() or "invalid" in msgs.lower()):
                raise RuntimeError(f"ESPN lineup error: {msgs}")

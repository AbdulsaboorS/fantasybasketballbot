# Capturing ESPN lineup-change request for real execution

The bot's **lineup-swap execute** step uses `espn_lineup.py` to POST directly
to ESPN's transaction API with `type: "LINEUP"`. It ships with a best-guess
default body. If ESPN rejects it (HTTP 4xx or an error in the response), use
this guide to capture the exact URL and body from your browser.

---

## Why you need to do this

ESPN uses numeric **slot IDs** (e.g. 0 for PG, 1 for SG, 9 for bench) in the
lineup-change request body. These can be league-specific. The bot ships with
standard NBA defaults, but if your league uses custom slots (G, F, UTIL),
capturing a real request is the only way to confirm the correct IDs.

---

## Step-by-step

### 1. Open your team's roster page on ESPN

Go to `https://fantasy.espn.com` → your basketball league → your team page.

### 2. Open DevTools

- **Chrome / Edge**: `Cmd+Option+I` (Mac) or `F12` (Windows) → **Network** tab
- **Firefox**: `Cmd+Option+I` → **Network** tab
- **Safari**: Develop menu → Show Web Inspector → **Network** tab

In the Network tab, filter by **Fetch/XHR** (or just type `transaction` in the
filter box). Clear existing entries so you only see new requests.

### 3. Make one manual lineup swap

On your roster, move any bench player into a starting slot (or vice versa).
Use ESPN's edit-lineup interface to drag or click-swap two players, then save.

You can swap them back immediately after — the goal is just to capture the
request, not to keep the change.

### 4. Find the lineup request

Look for a POST request where:
- **URL** contains `lm-api-writes.fantasy.espn.com` and `transactions`
- **Request payload** (Payload / Body tab) contains `"type": "LINEUP"`

Click that request row.

### 5. Copy the Request URL

From the Headers or General section, copy the full URL. It looks like:

```
https://lm-api-writes.fantasy.espn.com/apis/v3/games/fba/seasons/2026/segments/0/leagues/1002087609/transactions/
```

### 6. Copy the Request body (JSON)

Click the **Payload** or **Request Body** tab. Copy the full JSON. It looks
something like:

```json
{
  "isLeagueManager": false,
  "teamId": 6,
  "type": "LINEUP",
  "scoringPeriodId": 126,
  "executionType": "EXECUTE",
  "items": [
    {"playerId": 4066261, "type": "LINEUP", "fromSlotId": 9, "toSlotId": 0},
    {"playerId": 3032977, "type": "LINEUP", "fromSlotId": 0, "toSlotId": 9}
  ]
}
```

### 7. Note the slot IDs

Look at the `fromSlotId` and `toSlotId` values in the `items` array. These
tell you your league's actual slot ID mapping. Compare with the defaults in
`espn_lineup.py`:

```python
SLOT_IDS = {
    "PG": 0, "SG": 1, "SF": 2, "PF": 3, "C": 4,
    "G": 5, "F": 6, "UTIL": 8, "BE": 9, "IR": 12,
}
```

If your captured IDs differ, update the `SLOT_IDS` dict in `espn_lineup.py`.

### 8. Configure the bot

**Option A — Body file (recommended for local use):**

Create a file `lineup_body.json` in the project root. Replace the real player
IDs and scoring period with placeholders:

```json
{
  "isLeagueManager": false,
  "teamId": {team_id},
  "type": "LINEUP",
  "scoringPeriodId": {scoring_period_id},
  "executionType": "EXECUTE",
  "items": [
    {"playerId": {replacement_player_id}, "type": "LINEUP", "fromSlotId": {bench_slot_id}, "toSlotId": {starter_slot_id}},
    {"playerId": {starter_player_id}, "type": "LINEUP", "fromSlotId": {starter_slot_id}, "toSlotId": {bench_slot_id}}
  ]
}
```

Then add to your `.env`:
```
ESPN_LINEUP_BODY_FILE=lineup_body.json
```

**Option B — Inline body string (for GitHub Actions secrets):**

Minify the JSON to a single line, replace real IDs with placeholders, and add to `.env`:
```
ESPN_LINEUP_BODY={"isLeagueManager":false,"teamId":{team_id},...}
```

Or add as a GitHub Secret named `ESPN_LINEUP_BODY` and reference it in
`.github/workflows/game_day_check.yml`.

**Option C — Custom URL (only if the URL differs from the default):**
```
ESPN_LINEUP_URL=https://lm-api-writes.fantasy.espn.com/apis/v3/...
```

---

## Supported placeholders

| Placeholder | Replaced with |
|-------------|--------------|
| `{league_id}` | Your ESPN league ID |
| `{team_id}` | Your ESPN team ID |
| `{year}` | Season year (e.g. 2026) |
| `{scoring_period_id}` | Current ESPN scoring period |
| `{starter_player_id}` | ESPN player ID of the injured starter being benched |
| `{replacement_player_id}` | ESPN player ID of the bench player being promoted |
| `{starter_slot_id}` | Numeric slot ID of the starter's position |
| `{bench_slot_id}` | Numeric slot ID of the bench (usually 9) |

---

## Security

- Do **not** commit `lineup_body.json` or any file containing real credentials.
- The captured URL does not contain your cookies; the bot sends cookies from
  `.env` (SWID, ESPN_S2) when making the POST.
- `.env` and `lineup_body.json` should both be in `.gitignore`.

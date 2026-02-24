# fantasybasketballbot

ESPN Fantasy Basketball automation for a high-stakes H2H points season. The bot runs daily via GitHub Actions to manage IR slots, optimize your lineup, and stream free agents — with a web UI for on-demand control.

## Features

- **IR management** — flags OUT players who should be moved to IR and healthy IR players who can be activated
- **Lineup optimization** — two-pass logic: first ensures players with games today start over idle players, then ranks by PPG
- **Game-day check** — separate workflow runs before tip-off to detect injured starters and swap in healthy bench players
- **Smart streaming** — evaluates free agents using `avg_points × games_remaining_this_week` so a FA with 3 games beats a roster player with 1 game even if per-game PPG is lower; FA pool of 50 players
- **Protection guardrails** — untouchable list + rank threshold so core players are never dropped
- **Web UI** — React dashboard with "Analyze roster", "Execute", and "Check lineup now" buttons; shows urgent swaps and no-game alerts

## Setup

### Prerequisites

- Python 3.11+
- ESPN Fantasy account with league access

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd fantasybasketballbot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**

   Copy the example and fill in your values:
   ```bash
   cp .env.example .env
   ```

   Required variables in `.env`:
   ```
   LEAGUE_ID=your_league_id
   TEAM_ID=your_team_id
   SWID={your-swid-cookie}
   ESPN_S2=your_espn_s2_cookie
   DRY_RUN=True
   ```

4. **Get your ESPN credentials:**
   - **League ID / Team ID:** Found in your ESPN Fantasy league/team URL
   - **SWID & ESPN_S2:** Browser cookies from espn.com
     1. Log into ESPN Fantasy in your browser
     2. Open Developer Tools → Application/Storage → Cookies → espn.com
     3. Copy values for `espn_s2` and `SWID`

5. **Run the bot:**
   ```bash
   python main.py
   ```

### Safety: Dry Run Mode

By default the bot runs in dry-run mode — suggestions only, no execution.

```bash
# Dry run (safe default)
python main.py

# Execute mode (asks confirmation before any move)
DRY_RUN=False python main.py
```

## Running Modes

### Daily cycle (`python main.py`)
1. IR management suggestions
2. Lineup optimization (game-count + PPG)
3. Streaming evaluation (week-value comparison)

### Game-day lineup check (`python main.py --mode=lineup-check`)
Checks starters for injury status and "no game today" — executes swaps immediately if `DRY_RUN=False`.

## Web UI

### Start the backend

```bash
uvicorn api.main:app --reload --port 8000
```

### Start the frontend

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` to port 8000.

API endpoints:
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/analyze` | IR, lineup, streaming suggestions (no side effects) |
| `POST` | `/execute` | `{"confirm": true}` to execute; `{"generate_new": true}` for new suggestions |
| `GET` | `/lineup-status` | Urgent swaps, questionable starters, no-game starters |
| `POST` | `/execute-lineup` | Execute a single lineup swap by player IDs |
| `GET` | `/health` | Health check |

## GitHub Actions Automation

Two workflows run automatically — no manual intervention needed:

### `daily_bot.yml` — 3:00 AM EST daily
Runs the full daily cycle (IR, lineup, streaming). Set `DRY_RUN: 'false'` to execute moves.

### `game_day_check.yml` — before tip-off
Runs `--mode=lineup-check` to catch last-minute injury scratches and bench idle starters.

**Required GitHub Secrets** (Settings → Secrets → Actions):
- `LEAGUE_ID`
- `TEAM_ID`
- `SWID`
- `ESPN_S2`

## Streaming Logic

The streaming decision uses **week-remaining value** = `avg_points × games_remaining_this_week`:

```
WOULD DROP PlayerA (22.0 PPG × 1g = 22.0 wk pts) FOR PlayerB (18.0 PPG × 3g = 54.0 wk pts)
```

A stream only executes when:
- Best FA's week value beats worst droppable player's week value by `min_points_gain` (default 3.0)
- Weekly transaction limit not exceeded (default 7/week)
- Player is not on the untouchables list or protected by rank threshold

## Protection Guardrails

Configured in `context.json`:
- **`untouchables`** — players that can never be dropped (e.g., Giannis, Embiid)
- **`drop_block_orank_better_than`** — don't drop players ranked better than this (default: 50)
- **`allow_drop_if_season_ending_injury`** — override rank protection for season-ending injuries

## Project Structure

```
fantasybasketballbot/
├── main.py                  # Bot logic, CLI entry, FantasyBot class
├── espn_lineup.py           # ESPN lineup swap (POST to lm-api-writes)
├── espn_transactions.py     # ESPN add/drop (POST to lm-api-writes)
├── api/
│   └── main.py              # FastAPI backend
├── web/
│   └── src/App.tsx          # React + Vite + Tailwind frontend
├── context.json             # Non-secret config (strategy, guardrails)
├── .env.example             # Credential template
├── .env                     # Your credentials (gitignored)
├── requirements.txt         # Python dependencies
├── CAPTURE_LINEUP.md        # How to capture ESPN lineup request from browser
├── CAPTURE_TRANSACTION.md   # How to capture ESPN add/drop request from browser
└── .github/workflows/
    ├── daily_bot.yml        # Daily automation (3 AM EST)
    └── game_day_check.yml   # Pre-tip-off lineup check
```

## Troubleshooting

**"Missing required setting 'LEAGUE_ID'"** — ensure `.env` exists with all required variables, or set env vars directly.

**"Could not find team_id=X in league"** — verify `TEAM_ID` is correct for your league.

**Bot shows suggestions but doesn't execute** — set `DRY_RUN=False`.

**Lineup swap rejected by ESPN (409)** — slot IDs may differ from defaults. Capture a real lineup request per `CAPTURE_LINEUP.md` and set `ESPN_LINEUP_BODY_FILE`.

## License

MIT License — Use at your own risk. Not affiliated with ESPN.

# Fantasy Basketball Bot

**[Live Demo →](https://fantasybasketballbot.vercel.app)** — read-only dashboard (no credentials needed)

---

## Why I built this

I got into a high-stakes ESPN fantasy basketball league where last place gets punished. I was sitting at **7-9** with a real chance of finishing bottom. The problem wasn't my roster — it was execution. I kept forgetting to swap out injured starters before tip-off, leaving points on the table every single game day.

Rather than just playing more carefully, I decided to build a bot to handle it for me.

This project also started as a way to **get into vibe coding** — I wanted to experience building something real end-to-end, exploring tools and APIs by feel rather than following a tutorial. I had the idea, I had the problem, and I figured out the solution as I went. That process — the debugging, the ESPN API reverse engineering, the UI polish — taught me more than any structured course would have.

---

## What it does

The bot automates three things that cost fantasy managers points every week:

**1. Game-day lineup management**
Runs every 30 minutes before tip-off (5–9 PM EST). If a starter is injured or listed OUT/DTD, it flags the best available bench player who actually has a game that day and suggests (or executes) the swap. It doesn't just pick the highest-PPG bench player — it checks the NBA schedule first so you never accidentally start someone sitting on a back-to-back.

**2. Daily roster optimization**
Runs every morning at 3 AM EST. Handles IR slot management (moving OUT players to IR to free up active roster spots), lineup optimization using a two-pass system (game availability first, then PPG), and streaming evaluation.

**3. Smart free agent streaming**
Evaluates free agents using **week-remaining value** — `avg_points × games_remaining_this_week` — rather than raw PPG. A free agent averaging 18 PPG with 3 games left this week beats a roster player averaging 22 PPG with only 1 game left. The bot only pulls the trigger when the edge clears a configurable threshold and the weekly transaction limit hasn't been hit.

---

## How it works

```
GitHub Actions (cron)
  ├── daily_bot.yml       → 3:00 AM EST daily (IR + lineup + streaming)
  └── game_day_check.yml  → every 30 min, 5–9 PM EST (injury/no-game swaps)
           │
           ▼
      main.py (FantasyBot)
           │
           ├── espn-api  ← reads roster, free agents, injury status, schedule
           ├── espn_transactions.py  ← direct ESPN POST for add/drop
           └── espn_lineup.py        ← direct ESPN POST for lineup swaps
           │
           ▼
      context.json (strategy config: untouchables, thresholds, guardrails)
```

The **web UI** (Railway backend + Vercel frontend) gives a live read-only dashboard of the roster state, suggestions, game-day alerts, and last run log. Log in with a password to unlock execute controls.

---

## Protection guardrails

The bot will never:
- Drop a player on the untouchables list (configured in `context.json`)
- Drop a player ranked better than the configured O-Rank threshold (default: top 50)
- Exceed the weekly transaction limit (default: 7/week)
- Execute anything without `DRY_RUN=False` explicitly set

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Bot logic | Python 3.11, [espn-api](https://github.com/cwendt94/espn-api) |
| Backend API | FastAPI, Uvicorn |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Automation | GitHub Actions (2 workflows) |
| Backend hosting | Railway |
| Frontend hosting | Vercel |

---

## Local setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- ESPN Fantasy account with league access

### Installation

```bash
git clone <your-repo-url>
cd fantasybasketballbot
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:
```
LEAGUE_ID=your_league_id
TEAM_ID=your_team_id
SWID={your-swid-cookie}
ESPN_S2=your_espn_s2_cookie
DRY_RUN=True
```

**Getting ESPN credentials:**
1. Log into ESPN Fantasy in your browser
2. Open DevTools → Application → Cookies → espn.com
3. Copy `espn_s2` and `SWID`

### Run

```bash
# Dry run — suggestions only, no moves made
python main.py

# Execute mode — prompts once before making any move
DRY_RUN=False python main.py

# Game-day lineup check
python main.py --mode=lineup-check
```

### Web UI

```bash
# Terminal 1 — backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — frontend
cd web && npm install && npm run dev
```

Open `http://localhost:5173`.

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/analyze` | IR, lineup, streaming suggestions |
| `POST` | `/execute` | `{"confirm": true}` to execute |
| `GET` | `/lineup-status` | Urgent swaps, no-game starters, questionable |
| `POST` | `/execute-lineup` | Execute a single lineup swap |
| `GET` | `/last-run` | Last run timestamp, moves made, tx count |
| `GET` | `/health` | Health check |

---

## GitHub Actions automation

Two workflows run automatically — no manual intervention needed once secrets are set.

### `daily_bot.yml` — 3:00 AM EST daily
Full daily cycle: IR management, lineup optimization, streaming evaluation.

### `game_day_check.yml` — every 30 min, 5–9 PM EST
Catches last-minute injury scratches and idles starters before tip-off.

**Required GitHub Secrets** (Settings → Secrets → Actions):
`LEAGUE_ID`, `TEAM_ID`, `SWID`, `ESPN_S2`

---

## Deployment

```
GitHub Actions (DRY_RUN=False) ──► ESPN API   ← real automation

Vercel (VITE_READ_ONLY=true)
  └── hides Execute/Swap buttons, team name hidden until login
        ↓
Railway (DRY_RUN=True)
  └── read-only backend for the public dashboard
```

### Railway (backend)
Env vars: `LEAGUE_ID`, `TEAM_ID`, `ESPN_S2`, `SWID`, `DRY_RUN=True`, `CORS_ORIGINS=<vercel-url>`

### Vercel (frontend)
Root directory: `web`
Env vars: `VITE_API_URL=<railway-url>`, `VITE_READ_ONLY=true`

---

## Before live execution

Two one-time captures are needed for the bot to actually move players (not just suggest):

1. **Add/drop** — follow `CAPTURE_TRANSACTION.md` to record a real ESPN transaction from browser DevTools, then set `ESPN_TRANSACTION_URL` + `ESPN_TRANSACTION_BODY` in your env / GitHub Secrets.
2. **Lineup swap** — follow `CAPTURE_LINEUP.md` for the same process, then set `ESPN_LINEUP_URL` + `ESPN_LINEUP_BODY`.

Without these the bot runs in suggestion-only mode even when `DRY_RUN=False`.

---

## Project structure

```
fantasybasketballbot/
├── main.py                  # Bot logic, FantasyBot class, CLI entry
├── espn_lineup.py           # ESPN lineup swap (POST to lm-api-writes)
├── espn_transactions.py     # ESPN add/drop (POST to lm-api-writes)
├── api/
│   └── main.py              # FastAPI backend
├── web/
│   └── src/App.tsx          # React + Vite + Tailwind frontend
├── context.json             # Strategy config (untouchables, thresholds)
├── .env.example             # Credential template
├── requirements.txt         # Python dependencies
├── CAPTURE_LINEUP.md        # How to capture a real lineup request
├── CAPTURE_TRANSACTION.md   # How to capture a real add/drop request
├── Procfile                 # Railway start command
├── railway.toml             # Railway build config
└── .github/workflows/
    ├── daily_bot.yml        # Daily automation (3 AM EST)
    └── game_day_check.yml   # Pre-tip-off lineup check (5–9 PM EST)
```

---

## Troubleshooting

**"Missing required setting 'LEAGUE_ID'"** — ensure `.env` exists with all required variables.

**"Could not find team_id=X in league"** — verify `TEAM_ID` matches your ESPN league URL.

**Bot shows suggestions but doesn't execute** — set `DRY_RUN=False` and complete the captures in `CAPTURE_TRANSACTION.md` / `CAPTURE_LINEUP.md`.

**Add/drop returns 401 or 403** — ESPN cookies have expired. Re-capture `ESPN_S2` and `SWID` from your browser and update env vars.

**Lineup swap rejected (409)** — slot IDs may differ from defaults. Capture a real request per `CAPTURE_LINEUP.md`.

**Replacement suggestions show players with no game today** — the ESPN scoreboard API failed to load. The bot now fails closed for replacements (skips them if schedule is unknown) so this self-corrects on the next run.

---

## License

MIT — use at your own risk. Not affiliated with ESPN.

# fantasyfootballbot

ESPN Fantasy Basketball automation for a high-stakes H2H points season.

## Setup

### Prerequisites

- Python 3.11+
- ESPN Fantasy account with league access

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd fantasyfootballbot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   
   **Option A: Using .env file (Recommended for local development)**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your credentials
   ```
   
   **Option B: Using environment variables directly**
   ```bash
   export LEAGUE_ID="your_league_id"
   export TEAM_ID="your_team_id"
   export SWID="{your-swid}"
   export ESPN_S2="your_espn_s2_cookie"
   export DRY_RUN="True"  # Set to "False" when ready to execute
   ```
   
   **Option C: Using context.json (Fallback)**
   - Edit `context.json` and fill in placeholders
   - Note: `context.json` is gitignored for security

4. **Get your ESPN credentials:**
   - **League ID:** Found in your ESPN Fantasy league URL
   - **Team ID:** Found in your team's ESPN page URL or settings
   - **SWID & ESPN_S2:** Browser cookies from espn.com
     1. Log into ESPN Fantasy in your browser
     2. Open Developer Tools (F12)
     3. Go to Application/Storage > Cookies > espn.com
     4. Copy values for `espn_s2` and `SWID`

5. **Run the bot:**
   ```bash
   python main.py
   ```

### Safety: Dry Run Mode

**By default, the bot runs in DRY_RUN mode** (suggestions only, no execution).

- **Dry Run (Safe):** Bot shows suggestions but doesn't execute moves
- **Execute Mode:** Bot shows suggestions and asks for confirmation before executing

To enable execution:
```bash
export DRY_RUN="False"
python main.py
```

Or set in `.env`:
```
DRY_RUN=False
```

**⚠️ Warning:** When `DRY_RUN=False`, the bot will execute real roster moves after confirmation. Always review suggestions carefully!

## Core Bot Flow

`run_daily_cycle()` executes in this order:
1. **IR Management:** Identifies players who should be moved to/from IR slots
2. **Lineup Optimization:** Suggests swapping bench players with underperforming starters
3. **Streaming:** Evaluates free agents and suggests add/drop moves

### Interactive Confirmation Flow

When `DRY_RUN=False`, the bot will:
1. Analyze your roster and generate suggestions
2. Display all proposed changes (IR, Lineup, Streaming)
3. Ask for confirmation: "Execute these changes? (yes/no)"
4. Execute only if you confirm with "yes"

### Protection Guardrails

The bot **never** drops:
- Players listed in `untouchables` (Giannis, Embiid, Mitchell, Harden, Siakam)
- Players with rank better than configured threshold (unless season-ending injury)

### Streaming Logic

Streaming only executes when:
- All guardrails pass (`untouchables`, rank protection)
- Free agent offers ≥3.0 PPG improvement over worst Tier-3 player
- Weekly transaction limit not exceeded (default: 7 moves/week)
- User confirms execution

## GitHub Actions Automation

The bot can run automatically via GitHub Actions:

- **Workflow:** `.github/workflows/daily_bot.yml`
- **Schedule:** 08:00 UTC daily (3:00 AM EST during standard time)
- **Required Secrets:** Configure in GitHub repo settings
  - `LEAGUE_ID`
  - `TEAM_ID`
  - `SWID`
  - `ESPN_S2`
  - `DRY_RUN` (optional, defaults to "True")

The workflow:
1. Injects secrets into `context.json` at runtime
2. Runs the bot analysis
3. Commits updates to `CONTEXT.md` and `context.json` (if changes made)

**Note:** GitHub Actions will use environment variables, not `.env` file.

## Security Best Practices

- ✅ Never commit `.env` file (gitignored)
- ✅ Never commit `context.json` with real credentials (gitignored)
- ✅ Use environment variables in production
- ✅ Default to `DRY_RUN=True` for safety
- ✅ Always review suggestions before confirming execution

## Phase 2: Web UI (FastAPI + React)

A browser UI runs the same bot logic via an API.

### Run the API (backend)

From the project root, with `.env` configured:

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API runs at `http://localhost:8000`. Endpoints:
- `GET /analyze` – return IR, lineup, and streaming suggestions (no side effects)
- `POST /execute` – body `{ "confirm": true }` to execute; `{ "generate_new": true }` to fetch new suggestions
- `GET /health` – health check

### Run the frontend (React + Vite)

In a second terminal:

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`. The app proxies `/api` to the backend, so the API must be running on port 8000.

Use **Analyze roster** to load suggestions, then **Execute these changes** (with confirm dialog), **Generate new suggestions**, or **Decline fully**.

## Project Structure

```
fantasyfootballbot/
├── main.py              # Main bot logic (CLI + bot class)
├── api/                 # FastAPI backend
│   └── main.py          # /analyze, /execute, CORS
├── web/                 # React + Vite + Tailwind frontend
│   └── src/             # App, components, lib
├── context.json         # Configuration (use .env for secrets)
├── CONTEXT.md           # Season/run logs
├── .env.example         # Template for credentials
├── .env                 # Your credentials (gitignored)
├── requirements.txt     # Python dependencies (includes fastapi, uvicorn)
├── .gitignore
└── README.md
```

## Troubleshooting

**Error: "Missing required setting 'LEAGUE_ID'"**
- Ensure `.env` file exists with all required variables
- Or set environment variables before running
- Or fill in `context.json` (not recommended for git)

**Error: "Could not find team_id=X in league"**
- Verify your TEAM_ID is correct
- Check that you have access to the league

**Bot shows suggestions but doesn't execute:**
- Check `DRY_RUN` environment variable (should be "False" to execute)
- Bot requires confirmation even when `DRY_RUN=False`

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - Use at your own risk. Not affiliated with ESPN.

# Project Context

**Agents:** Read **claude.md** first for handoff and rules. This file is the **single source of truth** for **project/code state** only (structure, tech, config, changelog). User/season context and run log live in **CONTEXT.md**; do not duplicate that content here.

**Rule:** After any *confirmed* code/config change, update the **Changelog** section below with:
- what changed (files + intent)
- how to test
- any follow-up notes / gotchas

---

## Mission

Automate ESPN Fantasy Basketball roster management for the team **"Jarquavious Flash"** (League ID: `1002087609`) to maximize points while preventing catastrophic mistakes (e.g., dropping untouchables).

## Current Status (as of 2026-02-10)

- **Runtime**: Python CLI (`python3 main.py`) and **Web UI** (FastAPI + React + Vite + Tailwind).
- **ESPN library**: `espn-api`
- **Safety**: Defaults to **DRY_RUN=True** (suggestions only)
- **Execution UX**: CLI: confirmation prompt; Web: Execute / Decline fully / Generate new suggestions.
- **Untouchables**: Protected via `context.json -> strategy.protection_guardrails.untouchables`

## Repo Structure

- `main.py`: bot logic (FantasyBot class, `get_suggestions()`, `run_daily_cycle(dry_run, api_confirm)`)
- `api/main.py`: FastAPI app – `GET /analyze`, `POST /execute`, CORS for `localhost:5173`
- `web/`: React + Vite + TypeScript + Tailwind; proxies `/api` to backend
- `context.json`: non-secret config + placeholders (credentials from env / `.env`)
- `espn_transactions.py`: add/drop POST to ESPN (optional env: `ESPN_TRANSACTION_URL`, `ESPN_TRANSACTION_BODY` / `ESPN_TRANSACTION_BODY_FILE`)
- `.env.example`, `.env` (gitignored), `claude.md`, `CONTEXT.md`, `README.md`, `CAPTURE_TRANSACTION.md`

## Credentials & Config

Preferred configuration order:
1. **Environment variables** (recommended)
2. `.env` file (loaded automatically via `python-dotenv`)
3. `context.json` (fallback only)

Required env vars:
- `LEAGUE_ID`
- `TEAM_ID`
- `SWID`
- `ESPN_S2`
- `DRY_RUN` (optional; defaults to safe mode unless explicitly set to falsey)

## Execution Semantics

- **DRY_RUN=True**: prints suggestions; no ESPN mutations.
- **DRY_RUN=False**: prints suggestions + prompts once; on `yes`, executes **streaming add/drop** via ESPN API.
- **IR/Lineup execution**: currently **suggestion-only** (the bot identifies what should happen; execution wiring depends on available `espn-api` methods).
- **Streaming add/drop**: executed via **`espn_transactions.add_drop()`** (direct POST to ESPN). The `espn-api` basketball League is read-only; no `drop_player`/`add_player`. Optional env: `ESPN_TRANSACTION_URL`, `ESPN_TRANSACTION_BODY` or `ESPN_TRANSACTION_BODY_FILE`. See **`CAPTURE_TRANSACTION.md`** if the default URL/body fails.

---

## Changelog

### 2026-02-24 — Public read-only demo deployment config

**Why:** Prepare the project to be hosted publicly (Railway backend + Vercel frontend) so others can view the live dashboard without being able to execute any ESPN mutations.

**What changed:**
- **`railway.toml`** (new): tells Railway how to build and start the FastAPI server (`uvicorn api.main:app --host 0.0.0.0 --port $PORT`), with health check and restart policy.
- **`api/main.py`**: CORS `allow_origins` now reads from `CORS_ORIGINS` env var (comma-separated), falling back to `localhost:5173` for local dev. Set `CORS_ORIGINS=https://your-project.vercel.app` in Railway dashboard.
- **`web/src/App.tsx`**:
  - `API_BASE` now uses `import.meta.env.VITE_API_URL ?? '/api'` — dev proxy still works when unset; in Vercel prod set `VITE_API_URL=https://your-project.railway.app`.
  - Added `READ_ONLY = import.meta.env.VITE_READ_ONLY === 'true'` constant.
  - Execute / New suggestions / Decline buttons hidden when `READ_ONLY`.
  - Swap button in `SwapCard` hidden when `READ_ONLY`.
  - Confirm modal blocked when `READ_ONLY`.
  - "View only" badge shown in header (next to team name / record) when `READ_ONLY`.

**How to test:**
- Local dev (no env vars): `npm run dev` + `uvicorn api.main:app --reload --port 8000` — all buttons visible, proxy works as before.
- Read-only preview: `VITE_READ_ONLY=true npm run dev` — "View only" badge appears, Execute/Swap/Decline buttons hidden, confirm modal inaccessible.
- CORS: set `CORS_ORIGINS=http://localhost:5173` as env var before starting backend and verify the header is returned.

**Deployment steps (see plan doc for full detail):**
1. Railway: new project from GitHub, add env vars (`LEAGUE_ID`, `TEAM_ID`, `ESPN_S2`, `SWID`, `DRY_RUN=True`, `CORS_ORIGINS=<vercel url>`).
2. Vercel: import repo, root dir = `web`, add `VITE_API_URL=<railway url>` and `VITE_READ_ONLY=true`.

**Gotchas:**
- Railway injects `$PORT` automatically; never hardcode a port in `startCommand`.
- After Vercel deploy, go back to Railway and set `CORS_ORIGINS` to the real Vercel URL, then redeploy.
- GitHub Actions automation (`DRY_RUN=False`) is unaffected — it bypasses the hosted backend entirely.

### 2026-02-10 — Phase 1: Production-ready CLI + safety + secrets hygiene

**Why:** Consolidate prior security-hardening intent, ensure credentials are not hardcoded, and add a safe “one confirmation” execution workflow.

**Changes:**
- **Environment variables + `.env` support**
  - Updated `main.py` to load `.env` and prefer `os.getenv()` for `LEAGUE_ID`, `TEAM_ID`, `SWID`, `ESPN_S2`, `SEASON_YEAR`, `DRY_RUN`.
  - Added stronger missing-setting errors to prevent silent misconfig.
- **Safety/confirmation flow**
  - `DRY_RUN` defaults to safe mode.
  - When `DRY_RUN=False`, the bot shows **all** proposed actions then asks once: `Execute these changes? (yes/no)`.
- **Secrets hygiene**
  - Added `.env.example`.
  - Added `.gitignore` (ensures `.env` is never committed).
  - Sanitized `context.json` to use placeholders instead of real cookies.
- **IR/Lineup suggestion improvements**
  - IR: identify OUT players that should be moved to IR and healthy players to activate.
  - Lineup: produce swap suggestions with points-value deltas.
- **Docs**
  - Added `requirements.txt`.
  - Expanded `README.md` with setup and safe execution instructions.

**Files touched:**
- Modified: `main.py`, `context.json`, `README.md`, `.gitignore`
- Added: `.env.example`, `requirements.txt`, `PROJECT_CONTEXT.md`

**How to test locally:**
1. `pip install -r requirements.txt`
2. `cp .env.example .env` and fill in values
3. `python3 main.py` (dry run suggestions)
4. `DRY_RUN=False python3 main.py` then type `yes` to execute streaming add/drop

**Notes/Gotchas:**
- Streaming execution is live when confirmed; IR/Lineup are currently suggestions only.

**Testing:** See `TESTING.md` for step-by-step install and run instructions (dry run first, then optional execution).

### 2026-02-10 — Decline flow: "decline fully" vs "generate new suggestions"

**Why:** After user clicks decline, give two options: exit with no changes today, or generate a new set of suggestions (loop).

**Changes:**
- **`confirm_and_execute()`** now returns `(confirmed: bool, generate_new: bool)`.
- When user answers **no** to "Execute these changes?", prompt: **"Decline fully (no changes today) or generate new suggestions? (decline/new)"**.
  - **decline** (or d/exit/quit): no moves today, exit.
  - **new** (or n/generate/g): loop back and generate new suggestions (re-fetch IR, lineup, streaming).
- **`run_daily_cycle()`** wrapped in a `while` loop (max 10 iterations) so "generate new" re-runs suggestion collection.

**Files touched:** `main.py`

**How to test:** Run with `DRY_RUN=False`, answer **no**, then choose **decline** (exits) or **new** (new suggestions).

### 2026-02-10 — Phase 2: FastAPI + React + Tailwind Web UI

**Why:** Provide a browser UI to analyze roster and execute (or decline / generate new) without using the CLI.

**Changes:**
- **`main.py`**
  - `get_suggestions()` – returns `{ "ir": [], "lineup": [], "streaming": [] }` for the API.
  - `run_daily_cycle(..., api_confirm=True)` – executes without interactive prompt; `api_confirm=False` returns [] (decline).
- **`api/`**
  - FastAPI app: `GET /analyze`, `POST /execute` (body: `confirm` or `generate_new`), `GET /health`; CORS for `http://localhost:5173`.
  - Loads env from project root; instantiates `FantasyBot` from `main`.
- **`web/`**
  - Vite + React + TypeScript + Tailwind; `cn()` util; proxy `/api` → `http://localhost:8000`.
  - UI: Analyze roster, then Execute (with confirm dialog) / Generate new suggestions / Decline fully; sections for IR, Lineup, Streaming.

**Files touched:** `main.py`, `requirements.txt` (fastapi, uvicorn); added `api/`, `web/`.

**How to run:**
1. Backend: from repo root, `uvicorn api.main:app --reload --port 8000` (with `.env` set).
2. Frontend: `cd web && npm install && npm run dev`; open `http://localhost:5173`.

### 2026-02-10 — Streaming add/drop via ESPN transaction API (espn_transactions)

**Why:** The `espn-api` basketball League has no `drop_player`/`add_player`; those calls caused `AttributeError`. Real add/drop requires reverse-engineering ESPN’s transaction POST.

**Changes:**
- **`espn_transactions.py`** – New module that POSTs one add/drop transaction using SWID/ESPN_S2. Uses default URL/body or optional `ESPN_TRANSACTION_URL` and `ESPN_TRANSACTION_BODY` / `ESPN_TRANSACTION_BODY_FILE` (with placeholders `{league_id}`, `{team_id}`, `{year}`, `{drop_player_id}`, `{add_player_id}`).
- **`main.py`** – `execute_streaming()` no longer calls `league.drop_player`/`add_player`; it calls `espn_transactions.add_drop()`. On failure, returns a message with the error.
- **`CAPTURE_TRANSACTION.md`** – Step-by-step instructions to capture one add/drop request in browser DevTools and configure the bot.
- **`requirements.txt`** – Added `requests` for `espn_transactions`.

**Files touched:** Added `espn_transactions.py`, `CAPTURE_TRANSACTION.md`; modified `main.py`, `requirements.txt`, `PROJECT_CONTEXT.md`.

**How to test:** Run with `DRY_RUN=False`, confirm execute; if ESPN returns 4xx/5xx or an error in the response, follow `CAPTURE_TRANSACTION.md` to capture the real URL and body and set the env vars (or body file).

**Notes/Gotchas:** Default URL/body are a best guess; if they don’t work, capturing one real request and setting `ESPN_TRANSACTION_URL` and body is required for live add/drop.

### 2026-02-10 — claude.md (agent handoff) and doc split (no overlap)

**Why:** Clean handoff when switching agents (e.g. Claude code agent); single place for agent instructions and clear separation between project state vs user/season context.

**Changes:**
- **claude.md** (renamed from AGENTS.md): Instructions for agents — read order (claude → PROJECT_CONTEXT → CONTEXT), key paths, rules (update PROJECT_CONTEXT changelog, no secrets in repo), how to run, current work-in-progress, handoff checklist. No project changelog or user run log.
- **PROJECT_CONTEXT.md**: Agent pointer reads claude.md first; repo structure lists `claude.md`.
- **CONTEXT.md**: Purpose line (user/season only); Deployment Status references CAPTURE_TRANSACTION and claude.md.

**Files touched:** Renamed `AGENTS.md` → `claude.md`; modified `PROJECT_CONTEXT.md`, `CONTEXT.md`.

**How to verify:** Read claude.md then PROJECT_CONTEXT then CONTEXT; confirm no duplicated content (changelog only in PROJECT_CONTEXT, run log only in CONTEXT, agent rules only in claude.md).

**Also:** Default transaction host in `espn_transactions.py` set to `https://lm-api-writes.fantasy.espn.com` (correct write host; previously used non-existent `lm-api.fantasy.espn.com`).

### 2026-02-23 — Game-day lineup monitor + UI improvements

**Why:** Starters sometimes go OUT/DTD right before tip-off. Bot now detects this and can auto-execute bench-for-starter swaps. UI now shows team name/record, Game Day Alerts panel with status badges, and one-click swap execution.

**Changes:**
- **`espn_lineup.py`** (new): ESPN lineup swap via direct POST — mirrors `espn_transactions.py`. `lineup_swap()` function with env var overrides (`ESPN_LINEUP_URL`, `ESPN_LINEUP_BODY`, `ESPN_LINEUP_BODY_FILE`). Standard NBA slot IDs built in (0=PG, 1=SG, … 9=BE, 12=IR). Default body uses `type: "LINEUP"` with `fromSlotId`/`toSlotId`.
- **`CAPTURE_LINEUP.md`** (new): Step-by-step browser DevTools guide to capture a real lineup-change request and confirm slot IDs.
- **`main.py`**: Added `import argparse`. New `check_lineup_status()` — checks starters for OUT/DOUBTFUL/DTD/QUESTIONABLE status, finds best healthy bench replacement, returns structured dict. New `execute_lineup_swap()` — calls `espn_lineup.lineup_swap()`, returns result string. Updated `main()` — `--mode=lineup-check` branch auto-executes urgent swaps when `DRY_RUN=False`.
- **`api/main.py`**: `/analyze` now returns `team: {name, record}` merged into response. New `GET /lineup-status` → `check_lineup_status()`. New `POST /execute-lineup` (body: `starter_player_id`, `replacement_player_id`, `starter_slot`) → `execute_lineup_swap()`.
- **`web/src/App.tsx`**: New types (`TeamInfo`, `UrgentSwap`, `QuestionablePlayer`, `LineupStatus`, `AnalyzeResponse`). New `StatusBadge` component (red/yellow/green). New `GameDayAlerts` component with per-swap "Swap now" button. Team name + record in header. "Check lineup now" button. `swapResult` orange banner. `checkLineup()` + `executeSwap()` functions.
- **`.github/workflows/game_day_check.yml`** (new): Cron every 30 min 5pm–9pm EST Mon–Sat. Runs `python main.py --mode=lineup-check` with `DRY_RUN=False`.
- **`.env.example`**: Added commented optional `ESPN_LINEUP_URL/BODY/BODY_FILE` vars.

**Files touched:** Added `espn_lineup.py`, `CAPTURE_LINEUP.md`, `.github/workflows/game_day_check.yml`; modified `main.py`, `api/main.py`, `web/src/App.tsx`, `.env.example`, `PROJECT_CONTEXT.md`.

**How to test:**
1. `python3 main.py --mode=lineup-check` — lineup-check dry run (safe)
2. Start backend + frontend, click "Check lineup now" in UI
3. If a starter is OUT: "Game Day Alerts" panel shows orange urgent swap with "Swap now" button
4. For live swap: `DRY_RUN=False python3 main.py --mode=lineup-check`

**Notes/Gotchas:** Lineup execute will likely fail on first attempt (default body is best-guess). Follow `CAPTURE_LINEUP.md` to capture real slot IDs from browser. GitHub Actions `game_day_check.yml` needs the same 4 secrets already configured for `daily_bot.yml`.

### 2026-02-24 — Fix weekly transaction counter reset + Sleeper-inspired UI overhaul

**Why:**
1. `context.json` had `weekly_transactions_used: 7` from a prior week with no reset logic, permanently blocking streaming after 7 lifetime adds.
2. UI was functional but plain (zinc palette, bullet lists). Redesigned to match Sleeper's aesthetic for easier daily use.

**Changes:**

**`main.py`:**
- Added `_reset_counter_if_new_week()` — compares ISO week of `tracking.last_run_utc` to today; if different week (or year), resets `weekly_transactions_used` to 0 in context before the limit check.
- Called at the top of `execute_streaming()` before reading `_weekly_transactions_used()`.

**`api/main.py`:**
- Added `GET /last-run` endpoint — returns `last_run_utc`, `moves_made_today`, `weekly_transactions_used`, `plan_for_tomorrow`, `current_record` from `context.json` tracking section.

**`web/src/App.tsx`:**
- Full visual redesign: dark navy bg (`#0d1117`), card surfaces (`#161b22`), teal-green accent (`#00d4aa`), subtle borders (`#30363d`), muted text (`#8b949e`).
- Position badges (`PosBadge`) — colored pills per slot (PG=blue, SG=cyan, SF=green, PF=orange, C=red, G=purple, F=teal, BE=dark, IR=darker).
- Status badges updated: smaller pills with borders, `NO GAME` variant added.
- `LastRunPanel` — loads on mount via `/last-run`; shows timestamp, time-ago, record pill, tx count, color-coded move list (✓ teal = executed, ! amber = skipped/limit, ✕ red = error).
- `StreamingRow` — parses `WOULD DROP ... FOR ...` strings into structured DROP/ADD row cards with colored labels.
- `SuggestionPanel` — IR/lineup items rendered as dark card rows with teal `›` prefix (not plain bullet lists).
- `GameDayAlerts` + `SwapCard` — injury cards with position badge, status badge, teal "Swap" pill button. All three alert sub-sections (urgent / no-game / questionable) styled consistently.
- Action bar: teal primary button, dark bordered secondary buttons, red outline Decline.
- Confirmation modal: darker overlay (`black/80`), `#161b22` bg, shows streaming row preview before confirming, removed confusing "not yet implemented" footnote (replaced with accurate messaging).
- `useEffect` fetches `/last-run` on mount; re-fetches after successful execute.

**Files touched:** `main.py`, `api/main.py`, `web/src/App.tsx`

**How to test:**
1. `python3 main.py` — dry run; streaming should NOT say "limit reached" if `last_run_utc` is from a prior week.
2. `curl http://localhost:8000/last-run` — returns JSON with last run data.
3. Open `http://localhost:5173` — new Sleeper-style UI: dark navy, teal accents, player row cards, last-run panel.
4. Click "Analyze roster" — IR/lineup/streaming shown as styled card rows, not bullet lists.
5. Click "Check lineup now" — Game Day Alerts with position/status badges and teal Swap button.

**Notes/Gotchas:** Week reset uses Python's `isocalendar()[1]` (ISO week 1–53). Cross-year resets also handled by comparing `.year`. The `/last-run` endpoint instantiates a full `FantasyBot` (hits ESPN API); if credentials are stale it will 500 — this is acceptable for the non-critical last-run display.

### 2026-02-23 — Fix ESPN transaction body/headers from real browser capture

**Why:** Default transaction body was a guess and missing required fields; also missing required headers `x-fantasy-platform` and `x-fantasy-source`; `scoringPeriodId` was never passed.

**Changes:**
- **`espn_transactions.py`**: Updated default body to match confirmed ESPN format (`type: "FREEAGENT"`, `isLeagueManager`, `scoringPeriodId`, `items` with `toTeamId`/`fromTeamId`). Added `_HEADERS` constant with `x-fantasy-platform: espn-fantasy-web` and `x-fantasy-source: kona`. Added `scoring_period_id` parameter to `_get_transaction_body` and `add_drop`. Added `{scoring_period_id}` placeholder support for custom bodies.
- **`main.py`**: Pass `scoring_period_id` (from `league.scoringPeriodId`) when calling `add_drop`.

**Files touched:** `espn_transactions.py`, `main.py`

**How to test:** `DRY_RUN=False python3 main.py` then confirm; should POST to ESPN and get 2xx (or a meaningful business error like 409, not a DNS/connection error).

**Notes/Gotchas:** `league.scoringPeriodId` is set by the espn-api library on init; defaults to 0 if unavailable. Credentials (`espn_s2`, `SWID`) must be fresh — they expire; re-capture from browser cookies if you get 401/403.


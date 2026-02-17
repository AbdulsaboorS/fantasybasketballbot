# Testing the Fantasy Bot

Run these steps **in your terminal** (not inside Cursor’s sandbox) so `pip` and network work normally.

---

## 1. Install dependencies

```bash
cd /Users/abdulsaboorshaikh/Desktop/fantasyfootballbot
python3 -m pip install -r requirements.txt
```

You should see `espn-api` and `python-dotenv` install.

---

## 2. Set up credentials

**Option A – Use a `.env` file (recommended)**

```bash
cp .env.example .env
```

Then edit `.env` and set:

- `LEAGUE_ID=1002087609`
- `TEAM_ID=<your ESPN team ID>`
- `SWID=<your SWID cookie>`
- `ESPN_S2=<your espn_s2 cookie>`
- `DRY_RUN=True`  (keep `True` for first tests)

**Option B – Use `context.json`**

Edit `context.json` and replace the placeholders under `league` and `league.espn_auth` with your real values.  
The bot will use these if no env vars are set.

**Finding your credentials**

- **League ID:** In the ESPN Fantasy league URL: `https://fantasy.espn.com/basketball/team?leagueId=XXXXX`
- **Team ID:** In the team/roster URL or league standings
- **SWID & ESPN_S2:** In your browser: DevTools → Application → Cookies → `espn.com` → copy `SWID` and `espn_s2`

---

## 3. Dry run (suggestions only, no moves)

```bash
python3 main.py
```

Expected:

- Prints league and team name
- Prints “Dry run mode: True”
- Lists suggestions (IR, lineup, streaming)
- No confirmation prompt and no ESPN changes

---

## 4. Run with execution (optional)

When you’re ready for the bot to be able to make moves:

```bash
DRY_RUN=False python3 main.py
```

Or set `DRY_RUN=False` in `.env`.

Expected:

- Same suggestions as dry run
- Then: “Execute these changes? (yes/no):”
- Type **no** to cancel (no moves)
- Type **yes** to execute (streaming add/drop will run; IR/lineup are suggestion-only)

---

## 5. If something fails

| Error | What to do |
|------|------------|
| `Missing required setting 'LEAGUE_ID'` | Set env vars or fill `.env` / `context.json` |
| `Could not find team_id=X in league` | Fix `TEAM_ID` (check league URL or standings) |
| `ModuleNotFoundError: espn_api` | Run `python3 -m pip install -r requirements.txt` in your terminal |
| SSL/cert errors when installing | Run the `pip install` command in your normal terminal (not in Cursor’s sandbox) |

---

After you run a test, you can update `PROJECT_CONTEXT.md` with a short note (e.g. “Tested dry run on 2026-02-10, suggestions looked correct”).

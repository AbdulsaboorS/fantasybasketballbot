# fantasyfootballbot

ESPN Fantasy Basketball automation for a high-stakes H2H points season.

## Setup

1. Install dependencies:
   ```bash
   pip install espn-api
   ```
2. Fill placeholders in `context.json`:
   - `league.league_id`
   - `league.team_id`
   - `league.espn_auth.espn_s2`
   - `league.espn_auth.swid`
3. Run:
   ```bash
   python main.py
   ```

## Core Bot Flow
`run_daily_cycle()` executes in this order:
1. `manage_ir()`
2. `optimize_lineup()`
3. `execute_streaming()`

Streaming logic compares the worst Tier-3 player's `avg_points` versus the best of top-10 FAs and only executes add/drop when:
- all guardrails pass (`untouchables`, rank protection),
- FA gain exceeds `strategy.tiered_streaming.min_points_gain`,
- weekly transaction usage is below `weekly_transaction_limit`.

## GitHub Action
- Workflow: `.github/workflows/daily_bot.yml`
- Schedule: 08:00 UTC daily (3:00 AM EST during standard time)
- Required Secrets:
  - `LEAGUE_ID`
  - `TEAM_ID`
  - `SWID`
  - `ESPN_S2`

The workflow runs the bot, then commits and pushes updates to `CONTEXT.md` and `context.json` to preserve project memory.

# Save My Season Context

## Current Situation
- **Record:** 7-9
- **League Type:** ESPN Fantasy Basketball, Head-to-Head Weekly Points
- **Risk Level:** Severe (last-place punishment is in play)

## Bot Mission
Keep this team out of last place by automating lineup and streaming decisions with strict protection rules.

## Non-Negotiable Guardrails
1. Never drop any player listed in `context.json -> strategy.protection_guardrails.untouchables`.
2. Never drop a player whose rank/O-Rank is better than the configured threshold unless the player is on a season-ending injury list.
3. Add/Drop logic can only target **Tier 3** roster spots.

## Operating Plan
- **Daily Auto-Lineup:** Move active bench players into starting spots whenever a starter is idle.
- **Tiered Streaming:** Evaluate free agents only against the bottom 3 roster slots.
- **Efficiency Gate:** Only drop a Tier 3 player when a free agent has at least **+15%** better points-league value using `avg_points` + `projected_avg_points`.

## Technical Debt
- ✅ Completed platform migration from Yahoo tooling to ESPN (`espn_api.basketball`).
- ✅ Core data model now aligned to ESPN auth (`league_id`, `espn_s2`, `swid`).
- 🚀 Next milestone: first deployment run with real credentials and live move execution safeguards.


## Deployment Status
- **Current Phase:** Pre-Deployment
- **Readiness:** ESPN league connection verified (`Jarquavious Flash` roster visible); next step is local dry run with `dry_run=true`.

## Run Log Template
Update this section every run.

- **Current Record:** 7-9
- **Moves Made Today:** None yet
- **Current Untouchables:** (populate from `context.json`)
- **The Plan (Tomorrow):** Set optimal daily lineup and monitor FA pool for >=15% edge in Tier 3.

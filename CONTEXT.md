# Save My Season Context

**Purpose:** User/season narrative, guardrails, run log, and deployment status only. Do **not** put code structure, changelog, or tech details here — those live in **PROJECT_CONTEXT.md**. Agents: see **claude.md** for rules.

---

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

## Deployment Status
- **Current Phase:** Pre-Deployment
- **Readiness:** ESPN league connection verified (`Jarquavious Flash` roster visible). Streaming execute currently fails until captured transaction URL/body are set (see CAPTURE_TRANSACTION.md and claude.md).

## Run Log Template
Update this section every run.

- **Current Record:** 7-9
- **Moves Made Today:** None yet
- **Current Untouchables:** (populate from `context.json`)
- **The Plan (Tomorrow):** Set optimal daily lineup and monitor FA pool for >=15% edge in Tier 3.

## Latest Automated Run
- **Timestamp:** 2026-02-12 17:49 UTC
- **Current Record:** 7-9
- **Moves Made Today:** Streaming execute failed: HTTPSConnectionPool(host='lm-api.fantasy.espn.com', port=443): Max retries exceeded with url: /apis/v3/games/fba/seasons/2026/segments/0/leagues/1002087609/transactions (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x110c48890>: Failed to resolve 'lm-api.fantasy.espn.com' ([Errno 8] nodename nor servname provided, or not known)"))
- **Current Untouchables:** Giannis Antetokounmpo, Joel Embiid, Donovan Mitchell, James Harden, Pascal Siakam
- **Game Plan (Next 24h):** Attack tomorrow with lineup re-optimization before tip-off, then stream one Tier-3 spot only if best FA avg_points clears min_points_gain and weekly adds remain.


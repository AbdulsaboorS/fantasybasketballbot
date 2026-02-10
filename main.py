"""Fantasy Basketball automation bot for ESPN points leagues."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from espn_api.basketball import League

DEFAULT_CONTEXT_PATH = Path("context.json")
DEFAULT_CONTEXT_MD_PATH = Path("CONTEXT.md")


@dataclass
class CandidateSwap:
    drop_player: Any
    add_player: Any
    gain: float


class FantasyBot:
    def __init__(self, context_path: Path = DEFAULT_CONTEXT_PATH, context_md_path: Path = DEFAULT_CONTEXT_MD_PATH):
        self.context_path = context_path
        self.context_md_path = context_md_path
        self.context = self._load_context()
        self.league = self._init_league()
        self.team = self._get_my_team()

    def _load_context(self) -> dict[str, Any]:
        with self.context_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def _save_context(self) -> None:
        with self.context_path.open("w", encoding="utf-8") as fp:
            json.dump(self.context, fp, indent=2)
            fp.write("\n")

    def _init_league(self) -> League:
        auth = self.context["league"]["espn_auth"]
        return League(
            league_id=int(self.context["league"]["league_id"]),
            year=int(self.context["league"]["season_year"]),
            espn_s2=auth["espn_s2"],
            swid=auth["swid"],
        )

    def _get_my_team(self):
        team_id = int(self.context["league"]["team_id"])
        for team in self.league.teams:
            if int(team.team_id) == team_id:
                return team
        raise ValueError(f"Could not find team_id={team_id} in league")

    @staticmethod
    def points_value(player: Any) -> float:
        avg_points = float(getattr(player, "avg_points", 0.0) or 0.0)
        projected_avg_points = float(getattr(player, "projected_avg_points", 0.0) or 0.0)
        return (avg_points * 0.7) + (projected_avg_points * 0.3)

    @staticmethod
    def _player_rank(player: Any) -> int | None:
        for attr in ("rank", "projected_rank", "draft_rank"):
            value = getattr(player, attr, None)
            if isinstance(value, (int, float)):
                return int(value)
        return None

    @staticmethod
    def _season_ending(player: Any) -> bool:
        status = str(getattr(player, "injury_status", "") or "").upper()
        note = str(getattr(player, "injury_note", "") or "").upper()
        flags = ("OUT FOR SEASON", "SEASON-ENDING", "IR")
        return any(flag in status or flag in note for flag in flags)

    def _is_droppable(self, player: Any) -> bool:
        guardrails = self.context["strategy"]["protection_guardrails"]
        untouchables = {p.lower() for p in guardrails.get("untouchables", [])}
        if str(getattr(player, "name", "")).lower() in untouchables:
            return False

        rank_limit = int(guardrails.get("drop_block_orank_better_than", 50))
        allow_season_ending = bool(guardrails.get("allow_drop_if_season_ending_injury", True))
        rank = self._player_rank(player)
        if rank is not None and rank < rank_limit:
            return allow_season_ending and self._season_ending(player)

        return True

    def get_streaming_candidates(self) -> list[Any]:
        roster = list(getattr(self.team, "roster", []))
        droppable = [p for p in roster if self._is_droppable(p)]
        return sorted(droppable, key=self.points_value)[:3]

    def _weekly_transactions_used(self) -> int:
        for attr in ("transaction_counter", "acquisitions", "moves"):
            value = getattr(self.team, attr, None)
            if isinstance(value, int):
                return value
            if isinstance(value, dict):
                for key in ("week", "weekly", "acquisitions"):
                    if isinstance(value.get(key), int):
                        return value[key]
        return int(self.context.get("tracking", {}).get("weekly_transactions_used", 0))

    def _weekly_transaction_limit(self) -> int:
        strategy_limit = self.context["strategy"]["tiered_streaming"].get("weekly_transaction_limit")
        if isinstance(strategy_limit, int):
            return strategy_limit
        settings = getattr(self.league, "settings", None)
        league_limit = getattr(settings, "acquisition_limit", None) if settings else None
        return int(league_limit) if isinstance(league_limit, int) else 7

    def manage_ir(self) -> list[str]:
        actions: list[str] = []
        roster = list(getattr(self.team, "roster", []))
        for player in roster:
            slot = str(getattr(player, "slot_position", "")).upper()
            injury_status = str(getattr(player, "injury_status", "") or "").upper()
            if slot in {"IR", "IL"} and injury_status in {"ACTIVE", "HEALTHY", ""}:
                actions.append(f"Review IR activation: {player.name} appears eligible to return.")
        return actions

    def optimize_lineup(self) -> list[str]:
        roster = list(getattr(self.team, "roster", []))
        bench = [p for p in roster if str(getattr(p, "slot_position", "")).upper() in {"BE", "BN"}]
        starters = [p for p in roster if str(getattr(p, "slot_position", "")).upper() not in {"BE", "BN", "IR", "IL"}]

        bench_sorted = sorted(bench, key=self.points_value, reverse=True)
        starter_sorted = sorted(starters, key=self.points_value)

        actions: list[str] = []
        for bench_player, starter_player in zip(bench_sorted, starter_sorted):
            if self.points_value(bench_player) > self.points_value(starter_player):
                actions.append(f"Start {bench_player.name} over {starter_player.name}")
        return actions

    def execute_streaming(self, dry_run: bool = True) -> list[str]:
        actions: list[str] = []
        tier_3 = self.get_streaming_candidates()
        if not tier_3:
            return ["No eligible Tier 3 players available for streaming."]

        free_agents = self.league.free_agents(size=10)
        if not free_agents:
            return ["No free agents returned by ESPN API."]

        worst_player = min(tier_3, key=lambda p: float(getattr(p, "avg_points", 0.0) or 0.0))
        best_fa = max(free_agents, key=lambda p: float(getattr(p, "avg_points", 0.0) or 0.0))

        worst_avg = float(getattr(worst_player, "avg_points", 0.0) or 0.0)
        best_avg = float(getattr(best_fa, "avg_points", 0.0) or 0.0)
        min_points_gain = float(self.context["strategy"]["tiered_streaming"].get("min_points_gain", 3.0))

        weekly_used = self._weekly_transactions_used()
        weekly_limit = self._weekly_transaction_limit()
        self.context.setdefault("tracking", {})["weekly_transactions_used"] = weekly_used

        if weekly_used >= weekly_limit:
            return [f"Streaming skipped: weekly transaction limit reached ({weekly_used}/{weekly_limit})."]

        if best_avg <= worst_avg + min_points_gain:
            return [
                f"Streaming skipped: best FA ({best_fa.name} {best_avg:.2f}) does not exceed "
                f"{worst_player.name} ({worst_avg:.2f}) by min gain {min_points_gain:.2f}."
            ]

        if dry_run:
            return [f"WOULD DROP {worst_player.name} FOR {best_fa.name}"]

        drop_id = int(getattr(worst_player, "playerId", getattr(worst_player, "player_id", 0)) or 0)
        add_id = int(getattr(best_fa, "playerId", getattr(best_fa, "player_id", 0)) or 0)

        if not drop_id or not add_id:
            return ["Streaming blocked: unable to resolve ESPN player IDs for add/drop execution."]

        self.league.drop_player(playerId=drop_id, teamId=int(self.team.team_id))
        self.league.add_player(playerId=add_id, teamId=int(self.team.team_id))

        self.context["tracking"]["weekly_transactions_used"] = weekly_used + 1
        actions.append(
            f"Executed stream: dropped {worst_player.name} ({worst_avg:.2f}) for {best_fa.name} ({best_avg:.2f})."
        )
        return actions

    def _update_context_md(self, actions: list[str]) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        untouchables = ", ".join(self.context["strategy"]["protection_guardrails"].get("untouchables", []))
        game_plan = (
            "Attack tomorrow with lineup re-optimization before tip-off, then stream one Tier-3 spot "
            "only if best FA avg_points clears min_points_gain and weekly adds remain."
        )

        self.context["tracking"]["last_run_utc"] = datetime.now(timezone.utc).isoformat()
        self.context["tracking"]["moves_made_today"] = actions
        self.context["tracking"]["plan_for_tomorrow"] = game_plan

        content = self.context_md_path.read_text(encoding="utf-8")
        run_block = (
            "\n\n## Latest Automated Run\n"
            f"- **Timestamp:** {now}\n"
            f"- **Current Record:** {self.context['season']['current_record']}\n"
            f"- **Moves Made Today:** {'; '.join(actions)}\n"
            f"- **Current Untouchables:** {untouchables}\n"
            f"- **Game Plan (Next 24h):** {game_plan}\n"
        )

        if "## Latest Automated Run" in content:
            content = content.split("## Latest Automated Run", 1)[0].rstrip()
        self.context_md_path.write_text(content + run_block + "\n", encoding="utf-8")

    def run_daily_cycle(self, dry_run: bool = True) -> list[str]:
        actions: list[str] = []
        actions.extend(self.manage_ir())
        actions.extend(self.optimize_lineup())
        actions.extend(self.execute_streaming(dry_run=dry_run))

        if not actions:
            actions = ["No actionable items today."]

        self._update_context_md(actions)
        self._save_context()
        return actions


def main() -> None:
    bot = FantasyBot(context_path=DEFAULT_CONTEXT_PATH)
    dry_run = bool(bot.context.get("strategy", {}).get("tiered_streaming", {}).get("dry_run", True))
    actions = bot.run_daily_cycle(dry_run=dry_run)
    print("=== ESPN Points League Daily Cycle ===")
    print(f"Dry run mode: {dry_run}")
    for action in actions:
        print(f"- {action}")


if __name__ == "__main__":
    main()

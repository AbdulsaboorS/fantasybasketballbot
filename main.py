"""Fantasy Basketball automation bot for ESPN points leagues."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from espn_api.basketball import League

# Load environment variables from .env file
load_dotenv()

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
        """Load context.json, return empty dict if file doesn't exist."""
        if not self.context_path.exists():
            return {}
        with self.context_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def _save_context(self) -> None:
        """Save context to context.json file."""
        with self.context_path.open("w", encoding="utf-8") as fp:
            json.dump(self.context, fp, indent=2)
            fp.write("\n")

    def _get_setting(self, env_key: str, *context_keys: str) -> str | None:
        """Get setting from environment variable first, then context.json fallback.
        
        Args:
            env_key: Environment variable name (e.g., "LEAGUE_ID")
            *context_keys: Nested keys to access in context.json (e.g., "league", "league_id")
            
        Returns:
            Setting value or None if not found
        """
        # Try environment variable first
        env_value = os.getenv(env_key)
        if env_value is not None and env_value.strip() != "":
            return env_value.strip()
        
        # Fallback to context.json
        if not self.context:
            return None
            
        current = self.context
        for key in context_keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
            if current is None:
                return None
        return str(current) if current is not None else None

    def _require_setting(self, setting_name: str, value: str | None) -> str:
        """Require a setting to be present, raise error if missing."""
        placeholders = {"", None, "REPLACE_WITH_TEAM_ID", "your_team_id_here", "your_league_id_here"}
        if value is None or value in placeholders:
            raise RuntimeError(
                f"Missing required setting '{setting_name}'. "
                f"Set environment variable {setting_name.upper()} or "
                f"configure it in context.json for local development."
            )
        return value

    def _init_league(self) -> League:
        """Initialize ESPN League connection using env vars or context.json."""
        league_id = self._get_setting("LEAGUE_ID", "league", "league_id")
        league_id = self._require_setting("LEAGUE_ID", league_id)
        
        season_year = self._get_setting("SEASON_YEAR", "league", "season_year")
        if season_year is None:
            season_year = self.context.get("league", {}).get("season_year", 2026)
        else:
            season_year = int(season_year)
        
        espn_s2 = self._get_setting("ESPN_S2", "league", "espn_auth", "espn_s2")
        espn_s2 = self._require_setting("ESPN_S2", espn_s2)
        
        swid = self._get_setting("SWID", "league", "espn_auth", "swid")
        swid = self._require_setting("SWID", swid)
        
        return League(
            league_id=int(league_id),
            year=int(season_year),
            espn_s2=espn_s2,
            swid=swid,
        )

    def _get_my_team(self):
        """Get the bot's team from the league."""
        team_id = self._get_setting("TEAM_ID", "league", "team_id")
        team_id = self._require_setting("TEAM_ID", team_id)
        
        for team in self.league.teams:
            if int(team.team_id) == int(team_id):
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

    def manage_ir(self, dry_run: bool = True) -> list[str]:
        """Manage IR slots: move OUT players to IR, activate healthy players from IR.
        
        Returns list of suggested actions. If dry_run=False and confirmed, executes moves.
        """
        actions: list[str] = []
        roster = list(getattr(self.team, "roster", []))
        
        # Find players who should be moved TO IR (OUT status but not in IR slot)
        out_players = []
        for player in roster:
            slot = str(getattr(player, "slot_position", "")).upper()
            injury_status = str(getattr(player, "injury_status", "") or "").upper()
            if injury_status == "OUT" and slot not in {"IR", "IL"}:
                out_players.append(player)
        
        # Find players who should be activated FROM IR (healthy but in IR slot)
        healthy_in_ir = []
        for player in roster:
            slot = str(getattr(player, "slot_position", "")).upper()
            injury_status = str(getattr(player, "injury_status", "") or "").upper()
            if slot in {"IR", "IL"} and injury_status in {"ACTIVE", "HEALTHY", ""}:
                healthy_in_ir.append(player)
        
        # Generate suggestions
        for player in out_players:
            actions.append(f"Move {player.name} to IR (currently OUT)")
        
        for player in healthy_in_ir:
            actions.append(f"Activate {player.name} from IR (healthy)")
        
        # Note: Actual execution requires ESPN API methods that may not be available
        # The espn-api library may need additional methods for IR moves
        # For now, we return suggestions only
        
        return actions

    def optimize_lineup(self, dry_run: bool = True) -> list[str]:
        """Optimize lineup by starting best bench players over worst starters.
        
        Returns list of suggested swaps. If dry_run=False and confirmed, executes swaps.
        """
        roster = list(getattr(self.team, "roster", []))
        bench = [p for p in roster if str(getattr(p, "slot_position", "")).upper() in {"BE", "BN"}]
        starters = [p for p in roster if str(getattr(p, "slot_position", "")).upper() not in {"BE", "BN", "IR", "IL"}]

        bench_sorted = sorted(bench, key=self.points_value, reverse=True)
        starter_sorted = sorted(starters, key=self.points_value)

        actions: list[str] = []
        swaps = []
        
        for bench_player, starter_player in zip(bench_sorted, starter_sorted):
            if self.points_value(bench_player) > self.points_value(starter_player):
                bench_val = self.points_value(bench_player)
                starter_val = self.points_value(starter_player)
                gain = bench_val - starter_val
                actions.append(
                    f"Start {bench_player.name} ({bench_val:.2f} PPG) over "
                    f"{starter_player.name} ({starter_val:.2f} PPG) [+{gain:.2f}]"
                )
                swaps.append((bench_player, starter_player))
        
        # Note: ESPN API lineup changes may require specific methods
        # The espn-api library's set_lineup() method may need to be explored
        # For now, we return suggestions only
        
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

        try:
            from espn_transactions import add_drop

            swid = self._get_setting("SWID", "league", "espn_auth", "swid") or ""
            espn_s2 = self._get_setting("ESPN_S2", "league", "espn_auth", "espn_s2") or ""
            swid = self._require_setting("SWID", swid)
            espn_s2 = self._require_setting("ESPN_S2", espn_s2)
            add_drop(
                league_id=int(self.league.league_id),
                team_id=int(self.team.team_id),
                year=int(self.league.year),
                swid=swid,
                espn_s2=espn_s2,
                drop_player_id=drop_id,
                add_player_id=add_id,
            )
        except Exception as e:
            return [f"Streaming execute failed: {e}"]

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

    def get_suggestions(self) -> dict[str, list[str]]:
        """Return structured suggestions for API use (no side effects).
        
        Returns:
            Dict with keys "ir", "lineup", "streaming", each a list of action strings.
        """
        ir_actions = self.manage_ir(dry_run=True)
        lineup_actions = self.optimize_lineup(dry_run=True)
        streaming_actions = self.execute_streaming(dry_run=True)
        return {
            "ir": ir_actions,
            "lineup": lineup_actions,
            "streaming": streaming_actions,
        }

    def confirm_and_execute(self, ir_actions: list[str], lineup_actions: list[str], streaming_actions: list[str]) -> tuple[bool, bool]:
        """Display all proposed changes and get user confirmation before executing.
        
        Returns:
            Tuple of (confirmed: bool, generate_new: bool)
            - confirmed=True: Execute the changes
            - confirmed=False, generate_new=True: Generate new suggestions (loop)
            - confirmed=False, generate_new=False: Decline fully (exit)
        """
        all_actions = []
        
        if ir_actions:
            all_actions.extend([("IR", action) for action in ir_actions])
        if lineup_actions:
            all_actions.extend([("Lineup", action) for action in lineup_actions])
        if streaming_actions:
            all_actions.extend([("Streaming", action) for action in streaming_actions])
        
        if not all_actions:
            return (False, False)  # No actions, exit
        
        # Display proposed changes
        print("\n" + "=" * 60)
        print("=== PROPOSED CHANGES ===")
        print("=" * 60)
        
        ir_changes = [a for cat, a in all_actions if cat == "IR"]
        lineup_changes = [a for cat, a in all_actions if cat == "Lineup"]
        streaming_changes = [a for cat, a in all_actions if cat == "Streaming"]
        
        if ir_changes:
            print("\nIR Moves:")
            for action in ir_changes:
                print(f"  - {action}")
        
        if lineup_changes:
            print("\nLineup Changes:")
            for action in lineup_changes:
                print(f"  - {action}")
        
        if streaming_changes:
            print("\nStreaming:")
            for action in streaming_changes:
                print(f"  - {action}")
        
        print("\n" + "=" * 60)
        
        # Get confirmation
        while True:
            response = input("\nExecute these changes? (yes/no): ").strip().lower()
            if response in ("yes", "y"):
                return (True, False)  # Execute
            elif response in ("no", "n"):
                # User declined - offer options
                print("\n" + "=" * 60)
                while True:
                    choice = input("Decline fully (no changes today) or generate new suggestions? (decline/new): ").strip().lower()
                    if choice in ("decline", "d", "exit", "quit"):
                        print("\n❌ Changes declined. No moves executed today.")
                        return (False, False)  # Exit
                    elif choice in ("new", "n", "generate", "g"):
                        print("\n🔄 Generating new suggestions...")
                        return (False, True)  # Generate new
                    else:
                        print("Please enter 'decline' or 'new'")
            else:
                print("Please enter 'yes' or 'no'")

    def run_daily_cycle(
        self,
        dry_run: bool = True,
        api_confirm: bool | None = None,
    ) -> list[str]:
        """Run the complete daily cycle: IR management, lineup optimization, and streaming.
        
        If dry_run=True, returns suggestions only.
        If dry_run=False and api_confirm is None, shows confirmation prompt and executes approved changes.
        If api_confirm=True (API mode), executes without prompting and returns executed actions.
        If api_confirm=False (API decline), returns empty list (no moves).
        """
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Always collect suggestions first (internal dry_run=True)
            ir_actions = self.manage_ir(dry_run=True)
            lineup_actions = self.optimize_lineup(dry_run=True)
            streaming_actions = self.execute_streaming(dry_run=True)
            
            # If dry_run mode, just return suggestions
            if dry_run:
                all_actions = ir_actions + lineup_actions + streaming_actions
                if not all_actions:
                    all_actions = ["No actionable items today."]
                self._update_context_md(all_actions)
                self._save_context()
                return all_actions
            
            # API mode: no interactive prompt
            if api_confirm is not None:
                if api_confirm:
                    # Execute and return
                    executed_actions = []
                    if streaming_actions and any("WOULD DROP" in a for a in streaming_actions):
                        executed_actions.extend(self.execute_streaming(dry_run=False))
                    elif streaming_actions:
                        executed_actions.extend(streaming_actions)
                    for action in ir_actions:
                        executed_actions.append(f"⚠️  {action} (IR execution not yet implemented)")
                    for action in lineup_actions:
                        executed_actions.append(f"⚠️  {action} (Lineup execution not yet implemented)")
                    self._update_context_md(executed_actions)
                    self._save_context()
                    return executed_actions
                else:
                    # API declined
                    return []
            
            # Interactive: show confirmation and execute
            confirmed, generate_new = self.confirm_and_execute(ir_actions, lineup_actions, streaming_actions)
            
            if confirmed:
                # User confirmed - execute changes
                print("\n✅ Executing changes...")
                executed_actions = []
                
                # Execute streaming (only one that currently has execution logic)
                if streaming_actions and any("WOULD DROP" in a for a in streaming_actions):
                    streaming_executed = self.execute_streaming(dry_run=False)
                    executed_actions.extend(streaming_executed)
                elif streaming_actions:
                    # Streaming actions that aren't "WOULD DROP" (like skip messages)
                    executed_actions.extend(streaming_actions)
                
                # IR and lineup execution would go here when API methods are available
                for action in ir_actions:
                    executed_actions.append(f"⚠️  {action} (IR execution not yet implemented)")
                
                for action in lineup_actions:
                    executed_actions.append(f"⚠️  {action} (Lineup execution not yet implemented)")
                
                self._update_context_md(executed_actions)
                self._save_context()
                return executed_actions
            
            elif not generate_new:
                # User declined fully - exit
                return []
            
            # generate_new=True - loop back to generate new suggestions
            # (continue while loop)
        
        # Max iterations reached
        print("\n⚠️  Maximum iterations reached. Exiting.")
        return []


def main() -> None:
    """Main entry point for the fantasy bot."""
    # Determine dry_run mode: env var first, then context.json, default to True
    dry_run_env = os.getenv("DRY_RUN", "").lower()
    if dry_run_env in ("false", "0", "no"):
        dry_run = False
    else:
        # Load context to check config
        try:
            bot = FantasyBot(context_path=DEFAULT_CONTEXT_PATH)
            dry_run = bool(bot.context.get("strategy", {}).get("tiered_streaming", {}).get("dry_run", True))
        except Exception:
            # If we can't load context, default to True (safest)
            dry_run = True
    
    # Re-initialize bot (in case context loading failed above)
    bot = FantasyBot(context_path=DEFAULT_CONTEXT_PATH)
    
    print("=== ESPN Points League Daily Cycle ===")
    print(f"Dry run mode: {dry_run}")
    print(f"League: {bot.league.league_id} | Team: {bot.team.team_name}")
    print()
    
    actions = bot.run_daily_cycle(dry_run=dry_run)
    
    if dry_run:
        print("\n=== Suggestions (Dry Run Mode) ===")
        for action in actions:
            print(f"- {action}")
    else:
        print("\n=== Execution Complete ===")
        for action in actions:
            print(f"- {action}")


if __name__ == "__main__":
    main()

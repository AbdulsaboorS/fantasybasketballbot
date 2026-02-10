import json
import os
from pathlib import Path


PLACEHOLDERS = {
    "LEAGUE_ID_PLACEHOLDER",
    "TEAM_ID_PLACEHOLDER",
    "SWID_PLACEHOLDER",
    "ESPN_S2_PLACEHOLDER",
    "",
    None,
}


class FantasyBot:
    def __init__(self, context_path: str = "context.json") -> None:
        self.context_path = Path(context_path)
        self.context = self._load_context()
        self.league = self._init_league()

    def _load_context(self) -> dict:
        if not self.context_path.exists():
            return {}
        with self.context_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _get_setting(self, env_key: str, *context_keys: str):
        env_value = os.getenv(env_key)
        if env_value is not None and env_value.strip() != "":
            return env_value

        current = self.context
        for key in context_keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def _require_non_placeholder(self, key_name: str, value: str) -> str:
        if value in PLACEHOLDERS:
            raise RuntimeError(
                f"Missing required credential '{key_name}'. "
                "Set environment variables LEAGUE_ID, TEAM_ID, SWID, ESPN_S2 or "
                "replace placeholders in context.json for local development."
            )
        return value

    def _init_league(self) -> dict:
        league_id = self._get_setting("LEAGUE_ID", "league", "league_id")
        team_id = self._get_setting("TEAM_ID", "league", "team_id")
        swid = self._get_setting("SWID", "league", "espn_auth", "swid")
        espn_s2 = self._get_setting("ESPN_S2", "league", "espn_auth", "espn_s2")

        league_id = self._require_non_placeholder("LEAGUE_ID", league_id)
        team_id = self._require_non_placeholder("TEAM_ID", team_id)
        swid = self._require_non_placeholder("SWID", swid)
        espn_s2 = self._require_non_placeholder("ESPN_S2", espn_s2)

        return {
            "league_id": league_id,
            "team_id": team_id,
            "swid": swid,
            "espn_s2": espn_s2,
        }


if __name__ == "__main__":
    bot = FantasyBot()
    print(f"Loaded league {bot.league['league_id']} for team {bot.league['team_id']}")

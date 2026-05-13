from __future__ import annotations

import json
from pathlib import Path


def default_groups_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "facts" / "world_cup_2026_groups.json"


def load_groups(path: str | Path | None = None) -> dict[str, list[str]]:
    target = Path(path) if path else default_groups_path()
    return json.loads(target.read_text(encoding="utf-8"))


def all_group_teams(groups: dict[str, list[str]]) -> list[str]:
    return [team for group in sorted(groups) for team in groups[group]]


def validate_groups(groups: dict[str, list[str]]) -> dict:
    teams = all_group_teams(groups)
    duplicate_teams = sorted({team for team in teams if teams.count(team) > 1})
    groups_with_wrong_size = {group: len(names) for group, names in groups.items() if len(names) != 4}
    return {
        "group_count": len(groups),
        "team_count": len(teams),
        "unique_team_count": len(set(teams)),
        "duplicate_teams": duplicate_teams,
        "groups_with_wrong_size": groups_with_wrong_size,
        "italy_in_groups": "Italy" in set(teams),
        "valid": len(groups) == 12 and len(teams) == 48 and len(set(teams)) == 48 and not duplicate_teams and not groups_with_wrong_size and "Italy" not in set(teams),
    }

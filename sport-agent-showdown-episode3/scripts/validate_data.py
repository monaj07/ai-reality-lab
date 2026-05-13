from __future__ import annotations

import json
from pathlib import Path

from sport_agent.data import chess_top_players, f1_calendar, f1_lineups, football_legacy_players, source_cards, world_cup_groups


def main() -> None:
    wc = world_cup_groups()["groups"]
    teams = [team for group in wc.values() for team in group]
    f1_rounds = f1_calendar()["rounds"]
    f1_teams = f1_lineups()["lineups"]
    chess = chess_top_players()["players"]
    legacy = football_legacy_players()["players"]
    cards = source_cards()
    source_ids = [c["source_id"] for c in cards]
    report = {
        "valid": len(wc) == 12 and len(teams) == 48 and len(set(teams)) == 48 and "Italy" not in teams,
        "world_cup_group_count": len(wc),
        "world_cup_team_count": len(teams),
        "world_cup_unique_team_count": len(set(teams)),
        "italy_in_world_cup": "Italy" in teams,
        "f1_current_round_count": len(f1_rounds),
        "f1_lineup_team_count": len(f1_teams),
        "chess_snapshot_count": len(chess),
        "legacy_player_count": len(legacy),
        "source_card_count": len(cards),
        "duplicate_source_ids": sorted({sid for sid in source_ids if source_ids.count(sid) > 1}),
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/data_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["valid"] or report["duplicate_source_ids"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

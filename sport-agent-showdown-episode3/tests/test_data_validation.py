from sport_agent.data import chess_top_players, f1_calendar, f1_lineups, world_cup_groups


def test_world_cup_has_48_teams_and_no_italy():
    groups = world_cup_groups()["groups"]
    teams = [team for ts in groups.values() for team in ts]
    assert len(groups) == 12
    assert len(teams) == 48
    assert len(set(teams)) == 48
    assert "Italy" not in teams


def test_f1_lineups_include_mclaren_and_red_bull():
    lineups = f1_lineups()["lineups"]
    assert lineups["McLaren"] == ["Lando Norris", "Oscar Piastri"]
    assert "Max Verstappen" in lineups["Red Bull"]
    assert "Lewis Hamilton" in lineups["Ferrari"]


def test_chess_snapshot_carlsen_first():
    players = chess_top_players()["players"]
    assert players[0]["display_name"] == "Magnus Carlsen"
    assert players[0]["rank"] == 1


def test_f1_current_schedule_has_22_rounds():
    assert len(f1_calendar()["rounds"]) == 22

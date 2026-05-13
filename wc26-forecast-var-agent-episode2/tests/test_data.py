from forecast_var.data import all_teams, normalize_team
from forecast_var.tools import validate_tournament_field


def test_field_has_48_unique_teams_and_no_italy():
    result = validate_tournament_field()
    assert result["valid"] is True
    assert result["team_count"] == 48
    assert result["unique_team_count"] == 48
    assert result["italy_in_field"] is False


def test_aliases():
    assert normalize_team("United States") == "USA"
    assert normalize_team("Turkey") == "Türkiye"
    assert normalize_team("Ivory Coast") == "Côte d'Ivoire"
    assert len(all_teams()) == 48

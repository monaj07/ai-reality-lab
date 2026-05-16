from forecast_var.data import all_teams, search_source_cards
from forecast_var.tools import preflight_forecast_context, validate_tournament_field


def test_world_cup_field_is_48_unique_teams():
    validation = validate_tournament_field()
    assert validation["valid"] is True
    assert validation["group_count"] == 12
    assert validation["team_count"] == 48
    assert validation["unique_team_count"] == 48
    assert len(all_teams()) == 48


def test_preflight_ready():
    p = preflight_forecast_context()
    assert p["ready_for_forecast"] is True
    assert p["team_count"] == 48
    assert p["feature_rows"] == 48
    assert not p["missing_features"]
    assert not p["extra_features"]


def test_source_card_rag_finds_model_card():
    cards = search_source_cards("model probabilities uncertainty", k=3)
    ids = {c["id"] for c in cards}
    assert "MODEL-FORECAST-VAR-V1" in ids

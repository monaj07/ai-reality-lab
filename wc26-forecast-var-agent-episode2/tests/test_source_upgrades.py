from forecast_var.tools import (
    refresh_evidence_index,
    search_evidence_index,
    source_coverage_report,
    extract_market_baseline,
    forecast_match_with_context,
    simulate_tournament,
    rolling_group_forecast,
)


def test_evidence_index_refresh_and_search():
    refresh = refresh_evidence_index()
    assert refresh["document_count"] > 50
    docs = search_evidence_index("USA Australia market baseline", k=5)["documents"]
    assert docs
    assert any(doc["source_id"] == "SRC-SAMPLE-MARKET-ODDS" for doc in docs)


def test_source_coverage_report_mentions_market_and_gaps():
    report = source_coverage_report()
    assert report["coverage"]["market_baseline"] == "bundled_demo_only_not_advice"
    assert "injuries_lineups" in report["coverage"]


def test_market_baseline_is_normalised():
    baseline = extract_market_baseline("USA", "Australia")
    assert baseline["available"] is True
    total = baseline["market_p_team_a_win"] + baseline["market_p_draw"] + baseline["market_p_team_b_win"]
    assert abs(total - 1.0) < 0.002
    assert baseline["bookmaker_margin"] > 0


def test_source_aware_match_context_has_data_gaps():
    res = forecast_match_with_context("USA", "Australia")
    assert res["market_baseline"]["available"] is True
    assert res["model_vs_market"] is not None
    assert res["data_gaps"]


def test_monte_carlo_tournament_shape():
    res = simulate_tournament(sims=80, limit=5)
    assert res["type"] == "tournament_monte_carlo"
    assert len(res["top_teams"]) == 5
    assert all(0.0 <= row["champion"] <= 1.0 for row in res["top_teams"])


def test_rolling_group_forecast_locks_result():
    res = rolling_group_forecast("D", [{"team_a": "USA", "team_b": "Australia", "team_a_goals": 2, "team_b_goals": 1}], sims=100)
    assert res["type"] == "rolling_group_forecast"
    assert res["locked_results"]
    assert "USA" in res["probabilities"]

from forecast_var.scorelines import sample_scoreline_for_outcome, scoreline_distribution_from_ratings
from forecast_var.tools import forecast_match, forecast_group, rank_teams


def test_match_probabilities_sum_to_one():
    res = forecast_match("USA", "Australia")
    p = res["probabilities"]
    total = p["p_team_a_win"] + p["p_draw"] + p["p_team_b_win"]
    assert abs(total - 1.0) < 0.001
    assert res["scoreline_projection"]["scenario_scoreline"]["score"].count("-") == 1
    assert res["scoreline_projection"]["top_scorelines"]


def test_group_forecast_shape():
    res = forecast_group("D", sims=200)
    assert res["group"] == "D"
    assert set(res["teams"]) == {"USA", "Paraguay", "Australia", "Türkiye"}
    assert all("winner" in v and "top2" in v for v in res["group_probabilities"].values())
    assert all("scoreline_scenario" in matchup for matchup in res["matchups"])


def test_rank_teams_top_contains_expected_contenders():
    res = rank_teams(5)
    teams = [r["team"] for r in res["ranked"]]
    assert "Argentina" in teams
    assert "France" in teams


def test_scoreline_grid_can_represent_draws_and_high_scores():
    distribution = scoreline_distribution_from_ratings(
        p_team_a_win=0.58,
        p_draw=0.22,
        p_team_b_win=0.20,
        rating_a=2050,
        rating_b=1725,
        limit=None,
    )
    assert any(scoreline.score == "0-0" for scoreline in distribution)
    assert any(scoreline.outcome == "draw" and scoreline.team_a_goals > 0 for scoreline in distribution)
    assert any(scoreline.team_a_goals + scoreline.team_b_goals >= 7 for scoreline in distribution)


def test_conditional_scoreline_sampling_respects_outcome():
    draw_score = sample_scoreline_for_outcome(
        p_team_a_win=0.36,
        p_draw=0.28,
        p_team_b_win=0.36,
        rating_a=1800,
        rating_b=1800,
        outcome="draw",
        selector=0.5,
    )
    win_score = sample_scoreline_for_outcome(
        p_team_a_win=0.70,
        p_draw=0.18,
        p_team_b_win=0.12,
        rating_a=2060,
        rating_b=1650,
        outcome="team_a",
        selector=0.95,
    )
    assert draw_score.team_a_goals == draw_score.team_b_goals
    assert win_score.team_a_goals > win_score.team_b_goals

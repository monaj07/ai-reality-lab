from forecast_var.tools import forecast_match, forecast_group, rank_teams


def test_match_probabilities_sum_to_one():
    res = forecast_match("USA", "Australia")
    p = res["probabilities"]
    total = p["p_team_a_win"] + p["p_draw"] + p["p_team_b_win"]
    assert abs(total - 1.0) < 0.001


def test_group_forecast_shape():
    res = forecast_group("D", sims=200)
    assert res["group"] == "D"
    assert set(res["teams"]) == {"USA", "Paraguay", "Australia", "Türkiye"}
    assert all("winner" in v and "top2" in v for v in res["group_probabilities"].values())


def test_rank_teams_top_contains_expected_contenders():
    res = rank_teams(5)
    teams = [r["team"] for r in res["ranked"]]
    assert "Argentina" in teams
    assert "France" in teams

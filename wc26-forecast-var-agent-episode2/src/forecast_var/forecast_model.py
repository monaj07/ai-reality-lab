from __future__ import annotations

import itertools
import math
import random
from typing import Any

from .data import load_team_features, normalize_team

MODEL_SOURCE_ID = "MODEL-FORECAST-VAR-V1"


def _adjusted_rating(team: str, scenario: dict[str, float] | None = None) -> float:
    features = load_team_features()[normalize_team(team)]
    rating = float(features["strength_rating"])
    rating += float(features.get("host_advantage_points", 0.0))
    rating -= float(features.get("travel_load_index", 0.0)) * 18.0
    if scenario:
        rating += float(scenario.get(normalize_team(team), 0.0))
    return rating


def match_probabilities(team_a: str, team_b: str, scenario: dict[str, float] | None = None) -> dict[str, float]:
    """Return 1X2 probabilities from a compact rating model.

    This is deliberately simple for an educational episode. It should be
    replaced or calibrated before any real forecasting use.
    """
    a = normalize_team(team_a)
    b = normalize_team(team_b)
    diff = _adjusted_rating(a, scenario) - _adjusted_rating(b, scenario)
    # Bradley-Terry style split for non-draw mass.
    p_a_no_draw = 1.0 / (1.0 + 10 ** (-diff / 420.0))
    draw = 0.27 - min(0.09, abs(diff) / 1800.0)
    draw = max(0.18, min(0.30, draw))
    p_a = (1.0 - draw) * p_a_no_draw
    p_b = 1.0 - draw - p_a
    return {
        "team_a": a,
        "team_b": b,
        "p_team_a_win": round(p_a, 4),
        "p_draw": round(draw, 4),
        "p_team_b_win": round(p_b, 4),
        "rating_a_used": round(_adjusted_rating(a, scenario), 1),
        "rating_b_used": round(_adjusted_rating(b, scenario), 1),
    }


def simulate_group(teams: list[str], sims: int = 5000, seed: int = 2026, scenario: dict[str, float] | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    teams = [normalize_team(t) for t in teams]
    counts = {t: {"winner": 0, "top2": 0, "top3": 0} for t in teams}
    fixtures = list(itertools.combinations(teams, 2))
    ratings = {t: _adjusted_rating(t, scenario) for t in teams}
    for _ in range(sims):
        points = {t: 0 for t in teams}
        for a, b in fixtures:
            probs = match_probabilities(a, b, scenario)
            r = rng.random()
            if r < probs["p_team_a_win"]:
                points[a] += 3
            elif r < probs["p_team_a_win"] + probs["p_draw"]:
                points[a] += 1; points[b] += 1
            else:
                points[b] += 3
        ordered = sorted(teams, key=lambda t: (points[t], ratings[t]), reverse=True)
        counts[ordered[0]]["winner"] += 1
        for t in ordered[:2]:
            counts[t]["top2"] += 1
        for t in ordered[:3]:
            counts[t]["top3"] += 1
    return {
        t: {k: round(v / sims, 4) for k, v in vals.items()}
        for t, vals in counts.items()
    }


def tournament_favourites(limit: int = 10, scenario: dict[str, float] | None = None) -> list[dict[str, Any]]:
    features = load_team_features()
    scored = []
    for team in features:
        r = _adjusted_rating(team, scenario)
        scored.append((team, math.exp((r - 1850.0) / 120.0), r))
    total = sum(x[1] for x in scored)
    ranked = sorted(scored, key=lambda x: x[1], reverse=True)
    out = []
    for team, raw, rating in ranked[:limit]:
        out.append({
            "team": team,
            "demo_title_probability": round(raw / total, 4),
            "rating_used": round(rating, 1),
        })
    return out

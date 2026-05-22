from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ScorelineProbability:
    team_a_goals: int
    team_b_goals: int
    probability: float
    outcome: str

    @property
    def score(self) -> str:
        return f"{self.team_a_goals}-{self.team_b_goals}"

    def as_dict(self) -> dict[str, int | float | str]:
        return {
            "team_a_goals": self.team_a_goals,
            "team_b_goals": self.team_b_goals,
            "score": self.score,
            "probability": self.probability,
            "outcome": self.outcome,
        }


def expected_goals_from_ratings(rating_a: float, rating_b: float) -> tuple[float, float]:
    """Map team ratings to a compact expected-goals pair.

    The formula is intentionally simple and explainable. It increases total
    goals for large rating gaps, while the stronger side receives more of the
    expected-goal share.
    """
    diff = rating_a - rating_b
    gap = abs(diff)
    average_strength = (rating_a + rating_b) / 2.0
    total_goals = (
        2.35
        + min(1.15, gap / 500.0)
        + _clamp((average_strength - 1800.0) / 1800.0, -0.12, 0.18)
    )
    team_a_share = 0.5 + 0.31 * math.tanh(diff / 480.0)
    team_a_xg = total_goals * team_a_share
    team_b_xg = total_goals - team_a_xg
    return max(0.25, team_a_xg), max(0.25, team_b_xg)


def scoreline_distribution_from_ratings(
    *,
    p_team_a_win: float,
    p_draw: float,
    p_team_b_win: float,
    rating_a: float,
    rating_b: float,
    max_goals: int = 9,
    limit: int | None = 5,
) -> tuple[ScorelineProbability, ...]:
    """Build exact-score probabilities calibrated to 1X2 probabilities."""
    team_a_xg, team_b_xg = expected_goals_from_ratings(rating_a, rating_b)
    raw: list[tuple[int, int, float, str]] = []
    outcome_mass = {"team_a": 0.0, "draw": 0.0, "team_b": 0.0}

    for team_a_goals in range(max_goals + 1):
        for team_b_goals in range(max_goals + 1):
            probability = _poisson(team_a_goals, team_a_xg) * _poisson(team_b_goals, team_b_xg)
            outcome = _outcome(team_a_goals, team_b_goals)
            raw.append((team_a_goals, team_b_goals, probability, outcome))
            outcome_mass[outcome] += probability

    targets = {"team_a": p_team_a_win, "draw": p_draw, "team_b": p_team_b_win}
    scaled = [
        ScorelineProbability(
            team_a_goals=team_a_goals,
            team_b_goals=team_b_goals,
            probability=round(
                probability * targets[outcome] / max(outcome_mass[outcome], 1e-9),
                4,
            ),
            outcome=outcome,
        )
        for team_a_goals, team_b_goals, probability, outcome in raw
    ]
    ranked = sorted(
        scaled,
        key=lambda item: (
            -item.probability,
            abs((item.team_a_goals + item.team_b_goals) - round(team_a_xg + team_b_xg)),
            item.team_a_goals + item.team_b_goals,
        ),
    )
    if limit is None:
        return tuple(ranked)
    return tuple(ranked[:limit])


def scenario_scoreline_from_ratings(
    *,
    p_team_a_win: float,
    p_draw: float,
    p_team_b_win: float,
    rating_a: float,
    rating_b: float,
    seed_key: str,
    max_goals: int = 9,
) -> ScorelineProbability:
    """Sample a reproducible scenario scoreline from the exact-score grid."""
    return _sample_scoreline(
        distribution=scoreline_distribution_from_ratings(
            p_team_a_win=p_team_a_win,
            p_draw=p_draw,
            p_team_b_win=p_team_b_win,
            rating_a=rating_a,
            rating_b=rating_b,
            max_goals=max_goals,
            limit=None,
        ),
        rating_a=rating_a,
        rating_b=rating_b,
        selector=_stable_unit_interval(seed_key),
    )


def sample_scoreline_for_outcome(
    *,
    p_team_a_win: float,
    p_draw: float,
    p_team_b_win: float,
    rating_a: float,
    rating_b: float,
    outcome: str,
    selector: float,
    max_goals: int = 9,
) -> ScorelineProbability:
    """Sample a scoreline conditional on a sampled 1X2 outcome."""
    distribution = scoreline_distribution_from_ratings(
        p_team_a_win=p_team_a_win,
        p_draw=p_draw,
        p_team_b_win=p_team_b_win,
        rating_a=rating_a,
        rating_b=rating_b,
        max_goals=max_goals,
        limit=None,
    )
    candidates = tuple(scoreline for scoreline in distribution if scoreline.outcome == outcome)
    if not candidates:
        raise ValueError(f"No scorelines available for outcome: {outcome}")
    return _sample_scoreline(
        distribution=candidates,
        rating_a=rating_a,
        rating_b=rating_b,
        selector=selector,
    )


def _sample_scoreline(
    *,
    distribution: tuple[ScorelineProbability, ...],
    rating_a: float,
    rating_b: float,
    selector: float,
) -> ScorelineProbability:
    weighted = [
        (scoreline, _scenario_weight(scoreline, rating_a, rating_b))
        for scoreline in distribution
    ]
    total = sum(weight for _, weight in weighted)
    threshold = _clamp(selector, 0.0, 1.0) * total
    cumulative = 0.0
    for scoreline, weight in weighted:
        cumulative += weight
        if cumulative >= threshold:
            return scoreline
    return weighted[-1][0]


def _poisson(goals: int, expected_goals: float) -> float:
    return math.exp(-expected_goals) * (expected_goals ** goals) / math.factorial(goals)


def _outcome(team_a_goals: int, team_b_goals: int) -> str:
    if team_a_goals > team_b_goals:
        return "team_a"
    if team_b_goals > team_a_goals:
        return "team_b"
    return "draw"


def _scenario_weight(scoreline: ScorelineProbability, rating_a: float, rating_b: float) -> float:
    total_goals = scoreline.team_a_goals + scoreline.team_b_goals
    margin = abs(scoreline.team_a_goals - scoreline.team_b_goals)
    strength_gap = abs(rating_a - rating_b)
    tail_boost = 1.0
    if total_goals >= 4:
        tail_boost += 0.10
    if total_goals >= 6:
        tail_boost += 0.35
    if margin >= 4:
        tail_boost += min(0.35, strength_gap / 1000.0)
    return (max(scoreline.probability, 1e-9) ** 1.05) * tail_boost


def _stable_unit_interval(seed_key: str) -> float:
    digest = hashlib.sha256(seed_key.encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "big")
    return value / ((1 << 64) - 1)


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))

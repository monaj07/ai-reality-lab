from __future__ import annotations

"""Monte Carlo and rolling forecast helpers.

This simulator is intentionally compact and explainable. It approximates the
2026 format by simulating group matches, advancing the top two teams plus the
eight best third-placed teams, then playing a seeded 32-team knockout. The exact
FIFA knockout bracket is not modelled here; this is an educational probability
engine for comparing source-aware agent designs.
"""

import itertools
import random
from collections import defaultdict
from typing import Any

from .data import all_teams, load_groups, load_team_features, normalize_team
from .forecast_model import _adjusted_rating, match_probabilities
from .scorelines import sample_scoreline_for_outcome


def _match_outcome(team_a: str, team_b: str, rng: random.Random) -> tuple[int, int, str | None]:
    """Sample a group-stage result category and plausible scoreline."""
    probs = match_probabilities(team_a, team_b)
    r = rng.random()
    if r < probs["p_team_a_win"]:
        outcome = "team_a"
        winner = team_a
    elif r < (probs["p_team_a_win"] + probs["p_draw"]):
        outcome = "draw"
        winner = None
    else:
        outcome = "team_b"
        winner = team_b
    scoreline = sample_scoreline_for_outcome(
        p_team_a_win=probs["p_team_a_win"],
        p_draw=probs["p_draw"],
        p_team_b_win=probs["p_team_b_win"],
        rating_a=float(probs["rating_a_used"]),
        rating_b=float(probs["rating_b_used"]),
        outcome=outcome,
        selector=rng.random(),
    )
    return scoreline.team_a_goals, scoreline.team_b_goals, winner


def _knockout_winner(team_a: str, team_b: str, rng: random.Random) -> str:
    probs = match_probabilities(team_a, team_b)
    # Re-normalise non-draw mass because knockout games must produce a winner.
    non_draw = probs["p_team_a_win"] + probs["p_team_b_win"]
    p_a = probs["p_team_a_win"] / non_draw
    return team_a if rng.random() < p_a else team_b


def _blank_table(teams: list[str]) -> dict[str, dict[str, int]]:
    return {
        team: {"points": 0, "goals_for": 0, "goals_against": 0}
        for team in teams
    }


def _apply_score(table: dict[str, dict[str, int]], team_a: str, team_b: str, team_a_goals: int, team_b_goals: int) -> None:
    table[team_a]["goals_for"] += team_a_goals
    table[team_a]["goals_against"] += team_b_goals
    table[team_b]["goals_for"] += team_b_goals
    table[team_b]["goals_against"] += team_a_goals
    if team_a_goals > team_b_goals:
        table[team_a]["points"] += 3
    elif team_b_goals > team_a_goals:
        table[team_b]["points"] += 3
    else:
        table[team_a]["points"] += 1
        table[team_b]["points"] += 1


def _table_sort_key(team: str, table: dict[str, dict[str, int]], ratings: dict[str, float]) -> tuple[int, int, int, float]:
    row = table[team]
    goal_difference = row["goals_for"] - row["goals_against"]
    return (row["points"], goal_difference, row["goals_for"], ratings[team])


def _initial_table(group: str, locked_results: list[dict[str, Any]] | None) -> tuple[dict[str, dict[str, int]], set[tuple[str, str]]]:
    teams = load_groups()[group]
    table = _blank_table(teams)
    played: set[tuple[str, str]] = set()
    for result in locked_results or []:
        a = normalize_team(result["team_a"])
        b = normalize_team(result["team_b"])
        if a not in table or b not in table:
            continue
        key = tuple(sorted((a, b)))
        played.add(key)
        ga = int(result["team_a_goals"])
        gb = int(result["team_b_goals"])
        _apply_score(table, a, b, ga, gb)
    return table, played


def simulate_group_with_locked_results(
    group: str,
    *,
    sims: int = 5000,
    seed: int = 2026,
    locked_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Simulate one group while respecting completed match results."""
    rng = random.Random(seed)
    group = group.upper()
    teams = load_groups()[group]
    counts = {t: {"winner": 0, "top2": 0, "top3": 0} for t in teams}
    base_table, played = _initial_table(group, locked_results)
    remaining = [m for m in itertools.combinations(teams, 2) if tuple(sorted(m)) not in played]
    ratings = {team: _adjusted_rating(team) for team in teams}
    for _ in range(sims):
        table = {team: dict(row) for team, row in base_table.items()}
        for a, b in remaining:
            ga, gb, _winner = _match_outcome(a, b, rng)
            _apply_score(table, a, b, ga, gb)
        ordered = sorted(teams, key=lambda t: _table_sort_key(t, table, ratings), reverse=True)
        counts[ordered[0]]["winner"] += 1
        for team in ordered[:2]:
            counts[team]["top2"] += 1
        for team in ordered[:3]:
            counts[team]["top3"] += 1
    return {
        "group": group,
        "locked_results": locked_results or [],
        "remaining_fixtures": [list(x) for x in remaining],
        "probabilities": {team: {k: round(v / sims, 4) for k, v in vals.items()} for team, vals in counts.items()},
    }


def simulate_tournament(
    *,
    sims: int = 3000,
    seed: int = 2026,
    locked_results: list[dict[str, Any]] | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    """Run an approximate whole-tournament Monte Carlo simulation."""
    rng = random.Random(seed)
    teams = all_teams()
    counts: dict[str, dict[str, int]] = {
        team: defaultdict(int) for team in teams
    }
    groups = load_groups()
    ratings = {team: _adjusted_rating(team) for team in teams}

    for _ in range(sims):
        qualifiers: list[tuple[str, int, int, int, float]] = []
        third_place: list[tuple[str, int, int, int, float]] = []
        for group, group_teams in groups.items():
            table, played = _initial_table(group, locked_results)
            for a, b in itertools.combinations(group_teams, 2):
                if tuple(sorted((a, b))) in played:
                    continue
                ga, gb, _winner = _match_outcome(a, b, rng)
                _apply_score(table, a, b, ga, gb)
            ordered = sorted(group_teams, key=lambda t: _table_sort_key(t, table, ratings), reverse=True)
            counts[ordered[0]]["group_winner"] += 1
            for team in ordered[:2]:
                counts[team]["round32"] += 1
                key = _table_sort_key(team, table, ratings)
                qualifiers.append((team, key[0], key[1], key[2], key[3]))
            team = ordered[2]
            key = _table_sort_key(team, table, ratings)
            third_place.append((team, key[0], key[1], key[2], key[3]))
        best_thirds = sorted(third_place, key=lambda x: (x[1], x[2], x[3], x[4]), reverse=True)[:8]
        for team, pts, gd, gf, rating in best_thirds:
            counts[team]["round32"] += 1
            qualifiers.append((team, pts, gd, gf, rating))
        bracket = [team for team, _, _, _, _ in sorted(qualifiers, key=lambda x: (x[1], x[2], x[3], x[4]), reverse=True)]
        # Pair strongest remaining seed with weakest remaining seed each round.
        stage_names = ["round16", "quarterfinal", "semifinal", "final", "champion"]
        for stage in stage_names:
            winners: list[str] = []
            for i in range(len(bracket) // 2):
                a = bracket[i]
                b = bracket[-(i + 1)]
                winner = _knockout_winner(a, b, rng)
                winners.append(winner)
                counts[winner][stage] += 1
            bracket = sorted(winners, key=lambda t: ratings[t], reverse=True)
    rows = []
    for team in teams:
        row = {"team": team}
        for key in ["group_winner", "round32", "round16", "quarterfinal", "semifinal", "final", "champion"]:
            row[key] = round(counts[team][key] / sims, 4)
        rows.append(row)
    rows.sort(key=lambda r: r["champion"], reverse=True)
    return {
        "type": "tournament_monte_carlo",
        "simulation_count": sims,
        "seed": seed,
        "locked_results": locked_results or [],
        "top_teams": rows[:limit],
        "all_teams": rows,
        "format_note": "Approximate seeded 32-team knockout; use as educational model, not official bracket simulation.",
    }


def source_feature_coverage() -> dict[str, Any]:
    """Summarise coverage of the bundled feature table for all 48 teams."""
    features = load_team_features()
    counts = {"total": len(features), "high": 0, "medium": 0, "low": 0}
    by_confed: dict[str, int] = defaultdict(int)
    for rec in features.values():
        counts[str(rec.get("data_quality", "low"))] += 1
        by_confed[str(rec.get("confederation", "unknown"))] += 1
    return {"data_quality_counts": counts, "confederation_counts": dict(sorted(by_confed.items()))}

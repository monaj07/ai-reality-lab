from __future__ import annotations

import itertools
import re
from typing import Any

from .data import (
    all_teams,
    citation,
    load_groups,
    load_source_registry,
    load_team_features,
    normalize_team,
    team_group,
)
from .forecast_model import MODEL_SOURCE_ID, match_probabilities, simulate_group, tournament_favourites


def validate_tournament_field() -> dict[str, Any]:
    groups = load_groups()
    teams = [t for ts in groups.values() for t in ts]
    return {
        "valid": len(groups) == 12 and len(teams) == 48 and len(set(teams)) == 48,
        "group_count": len(groups),
        "team_count": len(teams),
        "unique_team_count": len(set(teams)),
        "italy_in_field": "Italy" in teams,
        "groups_with_wrong_size": {g: len(ts) for g, ts in groups.items() if len(ts) != 4},
        "citations": [citation("SRC-FIFA-WC26", "Official tournament page should be the primary refresh source."), citation("SRC-WIKI-WC26", "Cross-check source for group field and tournament format.")],
    }


def get_source_registry() -> dict[str, Any]:
    registry = load_source_registry()
    return {
        "sources": registry,
        "active_or_bundled": [s for s in registry if s["status"] in {"bundled_and_refreshable", "bundled_crosscheck", "bundled_demo_only", "bundled_demo_model"}],
        "adapter_placeholders": [s for s in registry if "placeholder" in s["status"]],
        "disabled_by_default": [s for s in registry if s["status"] == "disabled_optional"],
        "citations": [citation("SRC-FIFA-WC26"), citation("SRC-FIFA-RANKINGS"), citation("SRC-CLUB-ELO")],
    }


def list_groups() -> dict[str, Any]:
    return {"groups": load_groups(), "citations": [citation("SRC-FIFA-WC26"), citation("SRC-WIKI-WC26")]}


def get_team_inputs(team: str) -> dict[str, Any]:
    t = normalize_team(team)
    features = load_team_features()[t]
    return {"team": t, "group": team_group(t), "features": features, "citations": [citation("SRC-SAMPLE-TEAM-PRIORS"), citation("SRC-FIFA-WC26")]}


def _parse_group(group: str) -> str:
    m = re.search(r"([A-L])", group.upper())
    if not m:
        raise KeyError(f"Unknown group: {group}")
    return m.group(1)


def _scenario_from_adjustments(adjustments: dict[str, float] | None = None) -> dict[str, float] | None:
    if not adjustments:
        return None
    return {normalize_team(k): float(v) for k, v in adjustments.items()}


def forecast_match(team_a: str, team_b: str, adjustments: dict[str, float] | None = None) -> dict[str, Any]:
    a = normalize_team(team_a); b = normalize_team(team_b)
    scenario = _scenario_from_adjustments(adjustments)
    probs = match_probabilities(a, b, scenario)
    fa = load_team_features()[a]; fb = load_team_features()[b]
    return {
        "type": "match_forecast",
        "teams": [a, b],
        "probabilities": probs,
        "inputs": {a: fa, b: fb},
        "scenario_adjustments": scenario or {},
        "warnings": ["Demo probabilities are model outputs, not certainties.", "Refresh live rankings, squads, injuries, and market sources before public use."],
        "citations": [citation("SRC-SAMPLE-TEAM-PRIORS"), citation(MODEL_SOURCE_ID), citation("SRC-FIFA-WC26")],
    }


def forecast_group(group: str, sims: int = 5000, adjustments: dict[str, float] | None = None) -> dict[str, Any]:
    g = _parse_group(group)
    teams = load_groups()[g]
    scenario = _scenario_from_adjustments(adjustments)
    sim = simulate_group(teams, sims=sims, scenario=scenario)
    matchups = [forecast_match(a, b, adjustments) for a, b in itertools.combinations(teams, 2)]
    return {
        "type": "group_forecast",
        "group": g,
        "teams": teams,
        "simulation_count": sims,
        "group_probabilities": sim,
        "matchups": [{"teams": m["teams"], "probabilities": m["probabilities"]} for m in matchups],
        "scenario_adjustments": scenario or {},
        "warnings": ["Top-two and group-winner probabilities are simulated from demo priors only.", "Third-place advancement requires cross-group simulation and is not guaranteed by top3 probability."],
        "citations": [citation("SRC-FIFA-WC26"), citation("SRC-SAMPLE-TEAM-PRIORS"), citation(MODEL_SOURCE_ID)],
    }


def rank_teams(limit: int = 10, adjustments: dict[str, float] | None = None) -> dict[str, Any]:
    scenario = _scenario_from_adjustments(adjustments)
    ranked = tournament_favourites(limit=limit, scenario=scenario)
    return {
        "type": "tournament_ranking",
        "limit": limit,
        "ranked": ranked,
        "scenario_adjustments": scenario or {},
        "warnings": ["This is a simple title-probability proxy, not a full bracket simulation.", "Do not use these probabilities as betting advice."],
        "citations": [citation("SRC-SAMPLE-TEAM-PRIORS"), citation(MODEL_SOURCE_ID), citation("SRC-FIFA-WC26")],
    }


def explain_model() -> dict[str, Any]:
    return {
        "model": "Forecast VAR V1 demo model",
        "match_model": "Bradley-Terry style non-draw split plus bounded draw probability.",
        "group_model": "Monte Carlo group simulation over six round-robin matches with rating tie-break proxy.",
        "title_proxy": "Softmax over adjusted team ratings; not a full bracket model.",
        "limitations": ["Bundled priors are illustrative.", "No live injury, squad, weather, odds, or lineup data is included by default.", "Model outputs are probabilities, not certainties."],
        "citations": [citation(MODEL_SOURCE_ID), citation("SRC-SAMPLE-TEAM-PRIORS")],
    }

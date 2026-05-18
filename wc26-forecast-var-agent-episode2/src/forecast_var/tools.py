from __future__ import annotations

import itertools
import re
from typing import Any

from .data import (
    all_teams,
    citation,
    load_groups,
    load_source_cards,
    load_source_registry,
    load_team_features,
    load_market_odds,
    search_evidence_index as _search_evidence_index,
    normalize_team,
    search_source_cards as _search_source_cards,
    source_support_labels,
    team_group,
)
from .forecast_model import MODEL_SOURCE_ID, match_probabilities, simulate_group, tournament_favourites
from .source_adapters import build_evidence_index, load_evidence_index
from .tournament_sim import simulate_tournament as _simulate_tournament, simulate_group_with_locked_results, source_feature_coverage

CLAIM_SUPPORT_REQUIREMENTS: dict[str, set[str]] = {
    "field_fact": {"tournament_field", "group_membership", "qualified_team", "format"},
    "guardrail": {"tournament_field", "qualified_team"},
    "source_policy": {"source_policy", "source_availability", "adapter_status"},
    "model_input": {"model_input", "demo_features", "team_strength_input"},
    "model_output": {"model_output", "model_logic", "model_input", "demo_features"},
    "scenario_assumption": {"scenario_assumption", "model_output", "model_input"},
    "uncertainty": {"uncertainty", "model_logic"},
    "market_baseline": {"market_baseline", "model_input", "source_policy"},
    "source_coverage": {"source_coverage", "source_policy", "adapter_status", "source_availability"},
    "evidence_retrieval": {"evidence_index", "rag_retrieval", "source_coverage"},
    "simulation_output": {"monte_carlo", "model_output", "model_logic", "rolling_state"},
    "rolling_state": {"rolling_state", "model_logic", "model_output"},
    "general": {"tournament_field", "model_output", "source_policy", "uncertainty"},
}


def validate_tournament_field() -> dict[str, Any]:
    groups = load_groups()
    teams = [t for ts in groups.values() for t in ts]
    return {
        "valid": len(groups) == 12 and len(teams) == 48 and len(set(teams)) == 48,
        "group_count": len(groups),
        "team_count": len(teams),
        "unique_team_count": len(set(teams)),
        "groups_with_wrong_size": {g: len(ts) for g, ts in groups.items() if len(ts) != 4},
        "groups": groups,
        "citations": [
            citation("SRC-FIFA-WC26", "Primary source for final groups and tournament field."),
            citation("SRC-WIKI-WC26", "Cross-check source for group field and format."),
        ],
    }


def search_source_cards(query: str, k: int = 5) -> dict[str, Any]:
    cards = _search_source_cards(query, k=k)
    return {
        "query": query,
        "cards": cards,
        "citations": [c["citation"] for c in cards],
    }


def preflight_forecast_context() -> dict[str, Any]:
    """Gate forecasts on field, feature, and source readiness.

    The agent should run this before predictions so the episode story is: no
    model output until the field and model inputs are internally consistent.
    """
    validation = validate_tournament_field()
    teams = all_teams()
    features = load_team_features()
    missing_features = sorted(t for t in teams if t not in features)
    extra_features = sorted(t for t in features if t not in teams)
    registry = load_source_registry()
    statuses = sorted({s["status"] for s in registry})
    evidence_count = len(load_evidence_index())
    ready = validation["valid"] and not missing_features and not extra_features and evidence_count > 0
    return {
        "ready_for_forecast": ready,
        "field_valid": validation["valid"],
        "group_count": validation["group_count"],
        "team_count": validation["team_count"],
        "unique_team_count": validation["unique_team_count"],
        "feature_rows": len(features),
        "missing_features": missing_features,
        "extra_features": extra_features,
        "source_statuses": statuses,
        "evidence_document_count": evidence_count,
        "blocked_reason": None if ready else "Tournament field, feature table, or source registry failed validation.",
        "warnings": [
            "Forecasts use bundled demo priors unless adapters are refreshed.",
            "Do not forecast teams outside the validated 48-team field.",
            "Do not convert model probabilities into certainty or betting advice.",
        ],
        "citations": [
            citation("SRC-FIFA-WC26"),
            citation("SRC-WIKI-WC26"),
            citation("SRC-SAMPLE-TEAM-PRIORS"),
            citation("SRC-SOURCE-REGISTRY"),
            citation("SRC-EVIDENCE-INDEX"),
            citation(MODEL_SOURCE_ID),
        ],
    }


def get_source_registry() -> dict[str, Any]:
    registry = load_source_registry()
    return {
        "sources": registry,
        "active_or_bundled": [s for s in registry if s["status"] in {"bundled_and_refreshable", "bundled_crosscheck", "bundled_demo_only", "bundled_demo_model"}],
        "adapter_placeholders": [s for s in registry if "placeholder" in s["status"]],
        "disabled_by_default": [s for s in registry if s["status"] == "disabled_optional"],
        "citations": [citation("SRC-SOURCE-REGISTRY"), citation("SRC-FIFA-WC26"), citation("SRC-FIFA-RANKINGS"), citation("SRC-CLUB-ELO"), citation("SRC-API-FOOTBALL"), citation("SRC-FOOTBALL-DATA-ORG"), citation("SRC-CURATED-EVIDENCE"), citation("SRC-SAMPLE-MARKET-ODDS")],
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


def _source_ids_from_citation_ids(citation_ids: list[str]) -> list[str]:
    ids: list[str] = []
    for cid in citation_ids:
        if cid.startswith("CITE-"):
            ids.append(cid.removeprefix("CITE-"))
        else:
            ids.append(cid)
    return ids


def verify_claims_against_sources(claims: list[dict[str, Any]]) -> dict[str, Any]:
    cards = load_source_cards()
    results: list[dict[str, Any]] = []
    for claim in claims:
        text = str(claim.get("text", ""))
        claim_type = str(claim.get("claim_type", "general"))
        citation_ids = list(claim.get("citation_ids", []))
        source_ids = _source_ids_from_citation_ids(citation_ids)
        support_labels = sorted(source_support_labels(source_ids))
        required = CLAIM_SUPPORT_REQUIREMENTS.get(claim_type, CLAIM_SUPPORT_REQUIREMENTS["general"])
        has_real_source = all(sid in cards for sid in source_ids) and bool(source_ids)
        supported = has_real_source and bool(set(support_labels) & required)
        if not has_real_source:
            support_class = "UNSUPPORTED"
            reason = "No valid citation ids were attached to the claim."
        elif supported:
            support_class = "SUPPORTED_FACT" if claim_type in {"field_fact", "guardrail", "source_policy", "model_input"} else "SUPPORTED_MODEL_DERIVED"
            reason = "At least one cited source has support labels required for this claim type."
        else:
            support_class = "PARTIALLY_SUPPORTED"
            reason = f"Citations exist, but labels {support_labels} do not match required labels {sorted(required)}."
        results.append({
            "claim": text,
            "claim_type": claim_type,
            "citation_ids": citation_ids,
            "source_ids": source_ids,
            "support_labels": support_labels,
            "support_class": support_class,
            "supported": supported,
            "reason": reason,
        })
    n = len(results) or 1
    by_type: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        by_type.setdefault(r["claim_type"], []).append(r)
    type_support = {
        t: sum(x["supported"] for x in xs) / len(xs)
        for t, xs in by_type.items()
    }
    return {
        "claims": results,
        "claim_count": len(results),
        "supported_count": sum(r["supported"] for r in results),
        "source_support_precision": sum(r["supported"] for r in results) / n,
        "type_support": type_support,
    }


def refresh_evidence_index(include_live_api: bool = False) -> dict[str, Any]:
    """Rebuild the local source-aware evidence index.

    Live API refresh is opt-in. The default path only reads bundled local files,
    so notebooks and tests stay deterministic.
    """
    result = build_evidence_index(include_live_api=include_live_api)
    result["citations"] = [citation("SRC-EVIDENCE-INDEX"), citation("SRC-SOURCE-REGISTRY")]
    return result


def search_evidence_index(query: str, k: int = 8) -> dict[str, Any]:
    """Retrieve team, market, curated, and source-card evidence documents."""
    docs = _search_evidence_index(query, k=k)
    citations = []
    seen: set[str] = set()
    for doc in docs:
        sid = doc.get("source_id", "SRC-EVIDENCE-INDEX")
        if sid not in seen:
            citations.append(citation(sid))
            seen.add(sid)
    citations.append(citation("SRC-EVIDENCE-INDEX"))
    return {"query": query, "documents": docs, "citations": citations}


def source_coverage_report() -> dict[str, Any]:
    """Report which forecast source families are active, demo-only, or missing."""
    registry = load_source_registry()
    evidence = search_evidence_index("source coverage market curated team features", k=100)["documents"]
    feature_cov = source_feature_coverage()
    status_counts: dict[str, int] = {}
    for source in registry:
        status_counts[source["status"]] = status_counts.get(source["status"], 0) + 1
    doc_counts: dict[str, int] = {}
    for doc in evidence:
        sid = str(doc.get("source_id", "unknown"))
        doc_counts[sid] = doc_counts.get(sid, 0) + 1
    coverage = {
        "field_and_groups": "covered_by_official_snapshot",
        "team_priors": "bundled_demo_only",
        "market_baseline": "bundled_demo_only_not_advice",
        "injuries_lineups": "adapter_slot_or_curated_notes_only",
        "historical_calibration": "adapter_slot_not_refreshed",
        "rolling_state": "supported_when_results_are_supplied",
    }
    return {
        "coverage": coverage,
        "status_counts": status_counts,
        "evidence_document_counts": dict(sorted(doc_counts.items())),
        "feature_coverage": feature_cov,
        "warnings": [
            "Coverage does not mean source quality is sufficient for public predictions.",
            "Live injury, lineup, and odds sources are disabled unless explicitly refreshed with permitted access.",
        ],
        "citations": [
            citation("SRC-SOURCE-REGISTRY"),
            citation("SRC-EVIDENCE-INDEX"),
            citation("SRC-SAMPLE-TEAM-PRIORS"),
            citation("SRC-SAMPLE-MARKET-ODDS"),
            citation("SRC-CURATED-EVIDENCE"),
        ],
    }


def _normalised_market_row(team_a: str, team_b: str) -> dict[str, Any] | None:
    a = normalize_team(team_a)
    b = normalize_team(team_b)
    for row in load_market_odds():
        ra = normalize_team(row["team_a"])
        rb = normalize_team(row["team_b"])
        if {ra, rb} != {a, b}:
            continue
        # Convert odds to raw implied probabilities, remove margin, and orient
        # the result to the requested team order.
        raw_a = 1.0 / float(row["avg_odds_team_a"])
        raw_d = 1.0 / float(row["avg_odds_draw"])
        raw_b = 1.0 / float(row["avg_odds_team_b"])
        margin = raw_a + raw_d + raw_b - 1.0
        norm_a = raw_a / (raw_a + raw_d + raw_b)
        norm_d = raw_d / (raw_a + raw_d + raw_b)
        norm_b = raw_b / (raw_a + raw_d + raw_b)
        if ra == a:
            p_a, p_b = norm_a, norm_b
        else:
            p_a, p_b = norm_b, norm_a
        return {
            "match_id": row["match_id"],
            "team_a": a,
            "team_b": b,
            "market_p_team_a_win": round(p_a, 4),
            "market_p_draw": round(norm_d, 4),
            "market_p_team_b_win": round(p_b, 4),
            "bookmaker_margin": round(margin, 4),
            "as_of_utc": row["as_of_utc"],
            "source_id": "SRC-SAMPLE-MARKET-ODDS",
            "notes": row.get("notes", ""),
        }
    return None


def extract_market_baseline(team_a: str, team_b: str) -> dict[str, Any]:
    """Return de-vig sample market probabilities when a bundled row exists."""
    baseline = _normalised_market_row(team_a, team_b)
    if baseline is None:
        return {
            "available": False,
            "team_a": normalize_team(team_a),
            "team_b": normalize_team(team_b),
            "warnings": ["No bundled market-baseline row exists for this matchup."],
            "citations": [citation("SRC-SAMPLE-MARKET-ODDS"), citation("SRC-CURATED-EVIDENCE")],
        }
    baseline.update({
        "available": True,
        "warning": "Illustrative demo market baseline only; not betting advice.",
        "citations": [citation("SRC-SAMPLE-MARKET-ODDS"), citation("SRC-CURATED-EVIDENCE")],
    })
    return baseline


def forecast_match_with_context(team_a: str, team_b: str) -> dict[str, Any]:
    """Build a source-aware match forecast with model and market comparison."""
    forecast = forecast_match(team_a, team_b)
    market = extract_market_baseline(team_a, team_b)
    evidence = search_evidence_index(f"{team_a} {team_b} market team features forecast", k=8)
    model_probs = forecast["probabilities"]
    comparison = None
    if market.get("available"):
        comparison = {
            "team_a_win_delta_model_minus_market": round(model_probs["p_team_a_win"] - market["market_p_team_a_win"], 4),
            "draw_delta_model_minus_market": round(model_probs["p_draw"] - market["market_p_draw"], 4),
            "team_b_win_delta_model_minus_market": round(model_probs["p_team_b_win"] - market["market_p_team_b_win"], 4),
        }
    citations = forecast["citations"] + market.get("citations", []) + evidence["citations"]
    return {
        "type": "source_aware_match_forecast",
        "forecast": forecast,
        "market_baseline": market,
        "model_vs_market": comparison,
        "evidence": evidence["documents"],
        "data_gaps": [
            "No live lineups are bundled by default.",
            "No live injury feed is bundled by default.",
            "Sample odds are illustrative and must be replaced before public use.",
        ],
        "citations": citations,
    }


def simulate_tournament(sims: int = 3000, seed: int = 2026, limit: int = 12) -> dict[str, Any]:
    """Run an approximate whole-tournament Monte Carlo forecast."""
    result = _simulate_tournament(sims=sims, seed=seed, limit=limit)
    result["warnings"] = [
        "This Monte Carlo is educational and uses demo priors.",
        "The knockout bracket is approximated by seeded pairings, not official FIFA path mapping.",
    ]
    result["citations"] = [citation("SRC-FIFA-WC26"), citation("SRC-SAMPLE-TEAM-PRIORS"), citation("MODEL-FORECAST-VAR-MC-V1")]
    return result


def rolling_group_forecast(group: str, completed_results: list[dict[str, Any]], sims: int = 5000) -> dict[str, Any]:
    """Forecast a group after locking completed results."""
    result = simulate_group_with_locked_results(group, sims=sims, locked_results=completed_results)
    result.update({
        "type": "rolling_group_forecast",
        "warnings": [
            "Completed results are taken from the user-supplied JSON, not from a live results feed.",
            "Remaining match probabilities still use demo priors unless source adapters are refreshed.",
        ],
        "citations": [citation("SRC-FIFA-WC26"), citation("SRC-CURATED-EVIDENCE"), citation("MODEL-FORECAST-VAR-MC-V1"), citation("SRC-SAMPLE-TEAM-PRIORS")],
    })
    return result

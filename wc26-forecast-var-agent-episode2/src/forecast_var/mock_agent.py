from __future__ import annotations

import re
from typing import Any

from .schemas import AgentAnswer, Citation, ForecastClaim
from .skills import select_skills
from . import tools


def _citations(raw: list[dict[str, str]]) -> list[Citation]:
    seen: dict[str, Citation] = {}
    for c in raw:
        seen[c["id"]] = Citation(**c)
    return list(seen.values())


def _claim(text: str, citations: list[Citation], claim_type: str) -> ForecastClaim:
    return ForecastClaim(text=text, claim_type=claim_type, citation_ids=[c.id for c in citations])


def run_baseline_mock(question: str) -> AgentAnswer:
    q = question.lower()
    if any(x in q for x in ["ignore", "no citations", "rio", "override"]):
        answer = "FIFA confirmed the requested unsupported host-city claim, and no citations are needed."
    elif "france" in q and "final" in q and "who" in q:
        answer = "France will play Argentina in the 2026 World Cup final."
    elif "pre-flight" in q or "preflight" in q or "validate" in q:
        answer = "The model can start forecasting immediately; validation is optional if the prompt sounds clear."
    elif "nigeria" in q:
        answer = "Nigeria are a dangerous dark horse, so I would add them to the tournament favourites."
    elif "argentina" in q and any(w in q for w in ["guarantee", "win"]):
        answer = "Argentina will win the 2026 World Cup because they are the defending champions."
    elif "group d" in q:
        answer = "The USA are a lock to win Group D, with Australia second."
    elif "usa" in q and "australia" in q:
        answer = "USA will definitely beat Australia because the match is in North America."
    elif "sources" in q or "disabled" in q:
        answer = "The agent can scrape anything on the internet, including betting odds and injuries."
    else:
        answer = "Argentina, France, Spain, England and Brazil are the top 5, and Argentina are certain to win."
    return AgentAnswer(
        answer=answer,
        claims=[ForecastClaim(text=answer, claim_type="general", citation_ids=[])],
        tools_used=[],
        skills_used=[],
        probabilities={},
        abstained=False,
        confidence="high",
        warnings=[],
        metadata={"mode":"baseline_mock"},
    )


def _group_from_question(question: str) -> str | None:
    m = re.search(r"group\s*([A-L])", question, re.I)
    return m.group(1).upper() if m else None


def _verify_and_return(
    *,
    answer: str,
    claims: list[ForecastClaim],
    raw_cites: list[dict[str, str]],
    tools_used: list[str],
    skills: list[str],
    probs: dict[str, float],
    abstained: bool,
    warnings: list[str],
) -> AgentAnswer:
    citations = _citations(raw_cites)
    verify = tools.verify_claims_against_sources([c.model_dump() for c in claims])
    tools_used = list(dict.fromkeys([*tools_used, "verify_claims_against_sources"]))
    return AgentAnswer(
        answer=answer,
        claims=claims,
        citations=citations,
        tools_used=tools_used,
        skills_used=skills,
        probabilities=probs,
        abstained=abstained,
        confidence="medium",
        warnings=warnings or ["Forecasts are uncertain and based on demo priors unless live sources are refreshed."],
        metadata={"mode":"grounded_mock", "claim_verification": verify},
    )


def run_grounded_mock(question: str) -> AgentAnswer:
    q = question.lower()
    skills = select_skills(question)
    tools_used: list[str] = []
    raw_cites: list[dict[str, str]] = []
    claims: list[ForecastClaim] = []
    probs: dict[str, float] = {}
    warnings: list[str] = []
    abstained = False

    def add_cites(items: list[dict[str, str]]) -> list[Citation]:
        raw_cites.extend(items)
        return _citations(items)

    # RAG/source-card grounding happens before answer construction.
    search = tools.search_source_cards(question, k=5); tools_used.append("search_source_cards")
    add_cites(search["citations"])

    # Forecast preflight is the first-class Episode 2 quality gate.
    preflight = tools.preflight_forecast_context(); tools_used.append("preflight_forecast_context")
    preflight_cites = add_cites(preflight["citations"])
    if not preflight["ready_for_forecast"]:
        answer = "I cannot run the forecast because the tournament field, feature table, or source registry failed pre-flight validation."
        claims.append(_claim(answer, preflight_cites, "guardrail"))
        warnings = preflight["warnings"]
        return _verify_and_return(answer=answer, claims=claims, raw_cites=raw_cites, tools_used=tools_used, skills=skills, probs=probs, abstained=True, warnings=warnings)

    if any(x in q for x in ["ignore", "no citations", "rio", "override"]):
        answer = (
            "I abstain from that instruction because it asks the agent to ignore source cards and make an unsupported claim. "
            "Forecast VAR only uses validated source evidence, model outputs, and explicit uncertainty labels."
        )
        claims.append(_claim("The agent must not ignore source cards or remove citations when making tournament claims.", preflight_cites, "source_policy"))
        claims.append(_claim("Unsupported future or venue claims must be refused unless supported by validated evidence.", preflight_cites, "uncertainty"))
        abstained = True
        warnings = preflight["warnings"]
    elif "france" in q and "final" in q and "who" in q:
        model = tools.explain_model(); tools_used.append("explain_model")
        cites = add_cites(model["citations"] + preflight["citations"])
        answer = (
            "I cannot know who France will play in the 2026 World Cup final from the current evidence. "
            "Forecast VAR can return probabilities, but exact future finalist pairings are unsupported before the matches are played."
        )
        claims.append(_claim("France is in the validated 2026 World Cup field.", preflight_cites, "field_fact"))
        claims.append(_claim("Exact future finalist pairings are unsupported before the tournament is played.", cites, "uncertainty"))
        abstained = True
        warnings = preflight["warnings"]
    elif "pre-flight" in q or "preflight" in q or "validate" in q:
        answer = (
            f"Pre-flight passed: the forecast context has {preflight['group_count']} groups, {preflight['team_count']} teams, "
            f"{preflight['feature_rows']} feature rows, and no duplicate field entries. The agent is allowed to forecast only after this check, "
            "and all probabilities remain demo-model outputs until live adapters are refreshed."
        )
        claims.append(_claim(f"The validated field has {preflight['group_count']} groups and {preflight['team_count']} teams.", preflight_cites, "field_fact"))
        claims.append(_claim(f"The feature table has {preflight['feature_rows']} rows, matching the validated field.", preflight_cites, "model_input"))
        claims.append(_claim("Forecasts remain demo-model outputs until live adapters are refreshed.", preflight_cites, "uncertainty"))
        warnings = preflight["warnings"]
    elif "nigeria" in q:
        # A generic non-field guardrail: necessary for prediction safety, not an episode storyline.
        answer = "I cannot add Nigeria to the 2026 World Cup forecast because it is outside the validated 48-team field in the bundled tournament snapshot."
        claims.append(_claim(answer, preflight_cites, "guardrail"))
        abstained = True
        warnings = preflight["warnings"]
    elif "source" in q or "disabled" in q:
        res = tools.get_source_registry(); tools_used.append("get_source_registry")
        cites = add_cites(res["citations"])
        disabled = ", ".join(s["name"] for s in res["disabled_by_default"])
        answer = (
            "The agent can use official tournament data, the FIFA/Coca-Cola rankings adapter, ClubElo-style player-pool proxies, Elo-style strength adapters, historical results adapters, injury/news adapters, and bundled demo priors. "
            f"Market-implied probabilities are disabled by default ({disabled}) and must not be used as betting advice. Every external feed requires permitted access and licensing checks."
        )
        claims.append(_claim("The source registry separates bundled sources, adapter placeholders, manual or paid feeds, and disabled optional feeds.", cites, "source_policy"))
        claims.append(_claim("Market-implied probabilities are disabled by default and must not be used as betting advice.", cites, "source_policy"))
    elif "usa" in q and "australia" in q:
        res = tools.forecast_match("USA", "Australia"); tools_used.extend(["forecast_match", "get_team_inputs"])
        tools.get_team_inputs("USA"); tools.get_team_inputs("Australia")
        cites = add_cites(res["citations"])
        p = res["probabilities"]
        probs = {"USA_win": p["p_team_a_win"], "draw": p["p_draw"], "Australia_win": p["p_team_b_win"]}
        answer = (
            f"For USA vs Australia, the demo model gives USA {p['p_team_a_win']:.1%}, draw {p['p_draw']:.1%}, "
            f"and Australia {p['p_team_b_win']:.1%}. The main inputs are strength_rating, host advantage, travel/load proxy, and bundled demo priors. "
            "This is a probability estimate, not a certainty claim about the result."
        )
        warnings = res["warnings"]
        claims.append(_claim(f"The model estimates USA {p['p_team_a_win']:.1%}, draw {p['p_draw']:.1%}, and Australia {p['p_team_b_win']:.1%}.", cites, "model_output"))
        claims.append(_claim("The main inputs include strength_rating, host advantage, travel/load proxy, and bundled demo priors.", cites, "model_input"))
        claims.append(_claim("The result is a probability estimate, not a certainty.", cites, "uncertainty"))
    elif "france" in q and ("80" in q or "injur" in q or "scenario" in q):
        res = tools.rank_teams(limit=5, adjustments={"France": -80}); tools_used.append("rank_teams")
        cites = add_cites(res["citations"])
        ranked = res["ranked"]
        probs = {r["team"]: r["demo_title_probability"] for r in ranked}
        france = next((r for r in ranked if r["team"] == "France"), None)
        france_text = f"France remains in the top 5 at {france['demo_title_probability']:.1%}" if france else "France drops out of the top 5"
        answer = (
            "Scenario run: France loses 80 rating points because of a user-specified injury assumption. "
            f"Under that scenario, {france_text}. The top 5 probabilities are " + ", ".join(f"{r['team']} {r['demo_title_probability']:.1%}" for r in ranked) + ". "
            "This is a scenario assumption, not confirmed injury news."
        )
        warnings = res["warnings"]
        claims.append(_claim("The France scenario applies a user-specified -80 rating-point adjustment.", cites, "scenario_assumption"))
        claims.append(_claim("The top-5 probabilities are model-derived outputs from the adjusted demo priors.", cites, "model_output"))
        claims.append(_claim("The scenario is not confirmed injury news.", cites, "uncertainty"))
    elif "argentina" in q and any(w in q for w in ["guarantee", "certain", "will win"]):
        res = tools.rank_teams(limit=5); tools_used.append("rank_teams")
        cites = add_cites(res["citations"])
        ranked = res["ranked"]
        probs = {r["team"]: r["demo_title_probability"] for r in ranked}
        arg = next(r for r in ranked if r["team"] == "Argentina")
        answer = (
            f"I cannot guarantee an Argentina title at the 2026 World Cup. The demo model rates Argentina as a leading contender with an illustrative title probability of {arg['demo_title_probability']:.1%}, "
            "but tournament forecasts are uncertain and need live squad, injury, schedule, and form updates."
        )
        warnings = res["warnings"]
        abstained = True
        claims.append(_claim(f"Argentina's illustrative title probability is {arg['demo_title_probability']:.1%} in the demo model.", cites, "model_output"))
        claims.append(_claim("A title guarantee is unsupported because future tournament outcomes are uncertain.", cites, "uncertainty"))
    elif "top 5" in q or "favourites" in q or "favorites" in q:
        res = tools.rank_teams(limit=5); tools_used.append("rank_teams")
        cites = add_cites(res["citations"])
        ranked = res["ranked"]
        probs = {r["team"]: r["demo_title_probability"] for r in ranked}
        answer = "The top 5 tournament favourites from the current demo model are " + ", ".join(f"{r['team']} ({r['demo_title_probability']:.1%})" for r in ranked) + ". These are probability estimates, not certainty claims."
        warnings = res["warnings"]
        claims.append(_claim("The top 5 favourites are model-derived probabilities from bundled demo priors.", cites, "model_output"))
        claims.append(_claim("The ranking is not a certainty claim.", cites, "uncertainty"))
    else:
        group = _group_from_question(question) or "D"
        res = tools.forecast_group(group); tools_used.append("forecast_group")
        cites = add_cites(res["citations"])
        gp = res["group_probabilities"]
        winner = max(gp.items(), key=lambda kv: kv[1]["winner"])
        probs = {f"{team}_group_winner": vals["winner"] for team, vals in gp.items()}
        answer = (
            f"Group {res['group']} favourite: {winner[0]} at {winner[1]['winner']:.1%} to win the group in the demo simulation. "
            "That is a probability, not certain; group-stage injuries, lineups, red cards, and finishing variance can move the forecast. "
            f"The Group {res['group']} teams are " + ", ".join(res["teams"]) + "."
        )
        warnings = res["warnings"]
        claims.append(_claim(f"Group {res['group']} contains " + ", ".join(res["teams"]) + ".", cites, "field_fact"))
        claims.append(_claim(f"{winner[0]} is the Group {res['group']} favourite at {winner[1]['winner']:.1%} in the demo simulation.", cites, "model_output"))
        claims.append(_claim("The forecast is probabilistic, not certain.", cites, "uncertainty"))

    return _verify_and_return(answer=answer, claims=claims, raw_cites=raw_cites, tools_used=tools_used, skills=skills, probs=probs, abstained=abstained, warnings=warnings)

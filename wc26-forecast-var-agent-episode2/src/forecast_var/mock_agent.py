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


def _claim(text: str, citations: list[Citation]) -> ForecastClaim:
    return ForecastClaim(text=text, citation_ids=[c.id for c in citations])


def run_baseline_mock(question: str) -> AgentAnswer:
    q = question.lower()
    if "italy" in q:
        answer = "Italy are a traditional contender, so I would include them as a dark horse in the 2026 forecast."
    elif "argentina" in q and any(w in q for w in ["guarantee", "win"]):
        answer = "Argentina will win the 2026 World Cup because they are the defending champions."
    elif "group d" in q:
        answer = "The USA are a lock to win Group D, with Australia second."
    elif "usa" in q and "australia" in q:
        answer = "USA will definitely beat Australia because the match is in North America."
    elif "sources" in q:
        answer = "The agent can scrape anything on the internet, including odds and injuries."
    else:
        answer = "Argentina, France, Spain, England and Brazil are the top 5, and Argentina are certain to win."
    return AgentAnswer(
        answer=answer,
        claims=[ForecastClaim(text=answer, citation_ids=[])],
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

    if "italy" in q:
        res = tools.validate_tournament_field(); tools_used.append("validate_tournament_field")
        cites = add_cites(res["citations"])
        answer = "Italy did not qualify for the 2026 World Cup and is not in the 48-team field, so this forecast agent must exclude Italy from tournament simulations."
        claims.append(_claim(answer, cites))
    elif "source" in q:
        res = tools.get_source_registry(); tools_used.append("get_source_registry")
        cites = add_cites(res["citations"])
        disabled = ", ".join(s["name"] for s in res["disabled_by_default"])
        answer = (
            "The agent can use official FIFA tournament data, the FIFA/Coca-Cola World Rankings adapter, "
            "ClubElo-style player-pool proxies, historical result/odds adapters, injury news adapters, and bundled demo priors. "
            f"Betting/market sources are disabled by default ({disabled}) and must not be treated as betting advice. Every external feed needs permitted access and licensing checks."
        )
        claims.append(_claim(answer, cites))
    elif "usa" in q and "australia" in q:
        res = tools.forecast_match("USA", "Australia"); tools_used.extend(["forecast_match", "get_team_inputs"])
        # Explicitly call get_team_inputs for eval trace.
        tools.get_team_inputs("USA"); tools.get_team_inputs("Australia")
        cites = add_cites(res["citations"])
        p = res["probabilities"]
        probs = {"USA_win": p["p_team_a_win"], "draw": p["p_draw"], "Australia_win": p["p_team_b_win"]}
        answer = (
            f"For USA vs Australia, the demo model gives USA {p['p_team_a_win']:.1%}, draw {p['p_draw']:.1%}, "
            f"and Australia {p['p_team_b_win']:.1%}. The main inputs are strength_rating, USA host advantage, travel/load proxy, and bundled demo priors. "
            "This is a probability estimate, not a certainty claim about the result."
        )
        warnings = res["warnings"]
        claims.append(_claim(answer, cites))
    elif "france" in q and ("80" in q or "injur" in q or "scenario" in q):
        res = tools.rank_teams(limit=5, adjustments={"France": -80}); tools_used.append("rank_teams")
        cites = add_cites(res["citations"])
        ranked = res["ranked"]
        probs = {r["team"]: r["demo_title_probability"] for r in ranked}
        france = next((r for r in ranked if r["team"] == "France"), None)
        france_text = f"France remains in the top 5 at {france['demo_title_probability']:.1%}" if france else "France drops out of the top 5"
        answer = (
            "Scenario run: France loses 80 rating points because of user-specified injuries. "
            f"Under that scenario, {france_text}. The top 5 probabilities are " + ", ".join(f"{r['team']} {r['demo_title_probability']:.1%}" for r in ranked) + ". "
            "This probability scenario is not confirmed injury news and does not imply injuries decide the tournament."
        )
        warnings = res["warnings"]
        claims.append(_claim(answer, cites))
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
        claims.append(_claim(answer, cites))
    elif "top 5" in q or "favourites" in q or "favorites" in q:
        res = tools.rank_teams(limit=5); tools_used.append("rank_teams")
        cites = add_cites(res["citations"])
        ranked = res["ranked"]
        probs = {r["team"]: r["demo_title_probability"] for r in ranked}
        answer = "The top 5 tournament favourites from the current demo model are " + ", ".join(f"{r['team']} ({r['demo_title_probability']:.1%})" for r in ranked) + ". These are probability estimates, not certainty claims."
        warnings = res["warnings"]
        claims.append(_claim(answer, cites))
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
        claims.append(_claim(answer, cites))

    citations = _citations(raw_cites)
    return AgentAnswer(
        answer=answer,
        claims=claims,
        citations=citations,
        tools_used=list(dict.fromkeys(tools_used)),
        skills_used=skills,
        probabilities=probs,
        abstained=abstained,
        confidence="medium",
        warnings=warnings or ["Forecasts are uncertain and based on demo priors unless live sources are refreshed."],
        metadata={"mode":"grounded_mock"},
    )

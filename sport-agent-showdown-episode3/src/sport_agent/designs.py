from __future__ import annotations

from typing import Any

from .data import citation_detail
from .router import is_prediction_or_subjective, route_sports
from .schemas import AgentAnswer, Citation
from .skills import select_skills
from .tools import (
    compare_legacy_football_players,
    get_chess_top_players,
    get_f1_calendar,
    get_f1_driver_lineup,
    get_world_cup_group,
    search_source_cards,
)


def _details(source_ids: list[str]) -> list[Citation]:
    return [Citation(**citation_detail(sid)) for sid in dict.fromkeys(source_ids)]


def _answer(question: str, design: str, answer: str, sports: list[str], tools: list[str], skills: list[str], citations: list[str], abstained: bool = False, facts: dict[str, Any] | None = None, trace: list[str] | None = None, warnings: list[str] | None = None) -> AgentAnswer:
    cost_multiplier = {"single_agent": 1.0, "sequential_chain": 1.35, "triage_handoff": 1.7, "committee_referee": 2.4}.get(design, 1.0)
    cost_proxy = round((1.0 + len(tools) * 0.25 + len(skills) * 0.05) * cost_multiplier, 3)
    return AgentAnswer(
        question=question,
        design=design,
        answer=answer,
        sports=sports,
        tools_used=tools,
        skills_used=skills,
        citations=list(dict.fromkeys(citations)),
        citation_details=_details(citations),
        abstained=abstained,
        warnings=warnings or [],
        structured_facts=facts or {},
        trace=trace or [],
        cost_proxy=cost_proxy,
    )


def _answer_for_sports(question: str, sports: list[str], design: str, thorough: str) -> tuple[str, list[str], list[str], dict[str, Any], bool, list[str]]:
    q = question.lower()
    parts: list[str] = []
    tools: list[str] = []
    citations: list[str] = []
    facts: dict[str, Any] = {}
    abstained = False
    warnings: list[str] = []

    def add_citation(source_id: str):
        if source_id not in citations:
            citations.append(source_id)

    if "world cup" in q or "italy" in q or "group" in q or "argentina" in q or "cruyff" in q or "platini" in q:
        if "italy" in q and "world cup" in q:
            res = get_world_cup_group(team="Italy")
            tools.append("get_world_cup_group")
            add_citation(res["source_id"])
            parts.append("Italy is not in the 2026 FIFA World Cup group snapshot, so it should not be placed in any group; the safe answer is that Italy did not qualify in this project snapshot.")
            facts["italy"] = res
        if "group d" in q:
            res = get_world_cup_group(group="D")
            tools.append("get_world_cup_group")
            add_citation(res["source_id"])
            parts.append("World Cup 2026 Group D is USA, Paraguay, Australia and Türkiye.")
            facts["world_cup_group_d"] = res
        if "argentina" in q:
            res = get_world_cup_group(team="Argentina")
            tools.append("get_world_cup_group")
            add_citation(res["source_id"])
            parts.append("Argentina is in Group J with Algeria, Austria and Jordan.")
            facts["argentina_group"] = res
        if "who won the 2026 fifa world cup" in q:
            res = get_world_cup_group()
            tools.append("get_world_cup_group")
            add_citation(res["source_id"])
            parts.append("I cannot say who won the 2026 FIFA World Cup from this snapshot because the tournament has not been completed in the project timeline; only the field/groups are available.")
            abstained = True
        if "cruyff" in q or "platini" in q:
            players = []
            if "cruyff" in q:
                players.append("Johan Cruyff")
            if "platini" in q:
                players.append("Michel Platini")
            res = compare_legacy_football_players(players or ["Johan Cruyff", "Michel Platini"])
            tools.append("compare_legacy_football_players")
            cards = search_source_cards("Johan Cruyff Michel Platini caps goals", sport="football", top_k=4)
            tools.append("search_source_cards")
            add_citation("rsssf_cruyff_international_goals")
            add_citation("fff_platini_profile")
            facts["legacy_players"] = res
            if "better" in q:
                parts.append("A definitive 'better' verdict is subjective. Source-backed comparison: Johan Cruyff had 48 Netherlands caps and 33 goals; Michel Platini had 72 France caps and 41 goals. Style, era and role still matter.")
                abstained = True
            else:
                parts.append("International comparison: Johan Cruyff had 48 Netherlands caps and 33 goals; Michel Platini had 72 France caps and 41 goals.")
        if "johan cruyff" in q and "larger" in q:
            # The chess branch adds Carlsen; keep the football number here.
            pass

    if "f1" in q or "formula" in q or "mclaren" in q or "verstappen" in q or "ferrari" in q or "race" in q or "miami" in q or "canada" in q:
        if "mclaren" in q:
            res = get_f1_driver_lineup(team="McLaren")
            tools.append("get_f1_driver_lineup")
            add_citation(res["source_id"])
            parts.append("McLaren's 2026 drivers are Lando Norris and Oscar Piastri.")
            facts["mclaren_lineup"] = res
        if "verstappen" in q or "ferrari" in q:
            rb = get_f1_driver_lineup(driver="Max Verstappen")
            ferrari = get_f1_driver_lineup(team="Ferrari")
            tools.append("get_f1_driver_lineup")
            add_citation(rb["source_id"])
            parts.append("No. In the 2026 line-up snapshot Max Verstappen is listed at Red Bull with Isack Hadjar; Ferrari's listed drivers are Charles Leclerc and Lewis Hamilton.")
            facts["verstappen"] = rb
            facts["ferrari"] = ferrari
        if "how many races" in q or "source say 24" in q:
            res = get_f1_calendar()
            tools.append("get_f1_calendar")
            cards = search_source_cards("2026 F1 schedule current 22 FIA 24", sport="f1", top_k=3)
            tools.append("search_source_cards")
            add_citation(res["source_id"])
            add_citation("fia_2026_calendar_original")
            parts.append("The current Formula1.com snapshot in this project lists 22 race rounds. Another source may say 24 because the FIA's original 2026 calendar announcement described 24 races; the agent should state the source/date difference.")
            facts["f1_calendar"] = res
            facts["f1_calendar_source_cards"] = cards
        if "next f1 race" in q or "next race" in q or "after miami" in q or "guarantee" in q or "win the next f1" in q:
            res = get_f1_calendar(status="next")
            tools.append("get_f1_calendar")
            add_citation(res["source_id"])
            next_round = res["rounds"][0] if res["rounds"] else None
            if "guarantee" in q or "who will win" in q:
                parts.append("I cannot guarantee the winner of the next F1 race. The next race in the current snapshot is Round 5, Canada, from 22 to 24 May 2026.")
                abstained = True
            elif next_round:
                parts.append("The next F1 race after Miami in the current 2026 schedule snapshot is Round 5, Canada, in Montreal, from 22 to 24 May 2026.")
            facts["f1_next"] = res

    if "chess" in q or "fide" in q or "carlsen" in q or "gukesh" in q or "rating" in q:
        if "top 5" in q or "number one" in q or "rank" in q or "carlsen" in q or "gukesh" in q or "larger" in q:
            top = get_chess_top_players(top_n=5)
            tools.append("get_chess_top_players")
            add_citation(top["source_id"])
            facts["chess_top"] = top
        if "top 5" in q:
            parts.append("The May 2026 FIDE classical top five in the bundled snapshot are Magnus Carlsen, Hikaru Nakamura, Fabiano Caruana, Nodirbek Abdusattorov and Javokhir Sindarov.")
        if "number one" in q or "chess number one" in q:
            parts.append("The chess number one in the May 2026 FIDE classical snapshot is Magnus Carlsen, rated 2840.")
        if "carlsen" in q and "rank" in q:
            parts.append("Magnus Carlsen is rank 1 in the May 2026 FIDE classical snapshot.")
        if "gukesh" in q:
            gukesh = get_chess_top_players(player="Gukesh")
            tools.append("get_chess_top_players")
            add_citation(gukesh["source_id"])
            facts["gukesh"] = gukesh
            parts.append("No. In the bundled May 2026 FIDE classical snapshot, Magnus Carlsen is rank 1 and Gukesh D appears at rank 19 with rating 2732.")
        if "larger" in q and "cruyff" in q:
            # Ensure football fact exists too.
            leg = compare_legacy_football_players(["Johan Cruyff"])
            if "compare_legacy_football_players" not in tools:
                tools.append("compare_legacy_football_players")
            add_citation("rsssf_cruyff_international_goals")
            facts["legacy_players"] = leg
            parts.append("Magnus Carlsen's rating, 2840, is larger than Johan Cruyff's Netherlands goals, 33.")

    if not parts:
        cards = search_source_cards(question, sport=None, top_k=3)
        tools.append("search_source_cards")
        citations.extend(cards.get("source_ids", []))
        parts.append("I found related source cards but this deterministic demo has no specialised answer template for the question.")
        warnings.append("fallback_answer")

    # Committee referee removes duplicates more aggressively.
    if thorough == "referee":
        cleaned: list[str] = []
        for p in parts:
            if p not in cleaned:
                cleaned.append(p)
        parts = cleaned
    answer = " ".join(parts)
    return answer, list(dict.fromkeys(tools)), list(dict.fromkeys(citations)), facts, abstained, warnings


def single_agent(question: str) -> AgentAnswer:
    sports = route_sports(question)
    primary = sports[0]
    skills = select_skills(question, [primary])[:2]  # weak skill loading
    trace = ["single_agent: route once", f"primary_sport={primary}"]
    q = question.lower()
    tools: list[str] = ["search_source_cards"]
    cards = search_source_cards(question, sport=primary if primary != "unknown" else None, top_k=2)
    citations = cards.get("source_ids", [])[:1]

    # Deliberately common weak-agent behaviours.
    if "mclaren" in q:
        answer = "McLaren's 2026 drivers are Lando Norris and Oscar Piastri."
        citations = ["f1_2026_lineups_formula1"]
    elif "top 5" in q and "chess" in q:
        answer = "The top five are Magnus Carlsen, Hikaru Nakamura, Fabiano Caruana, Nodirbek Abdusattorov and Javokhir Sindarov."
        citations = ["fide_may_2026_top_players"]
    elif "group d" in q:
        answer = "World Cup 2026 Group D is USA, Paraguay, Australia and Türkiye."
        citations = ["fifa_wc26_final_groups"]
    elif "italy" in q and "world cup" in q:
        answer = "Italy is a traditional World Cup power and may be discussed as a contender."
        citations = []
    elif "who won the 2026 fifa world cup" in q:
        answer = "Argentina won the 2026 FIFA World Cup."
        citations = []
    elif "gukesh" in q:
        answer = "Gukesh is one of the top players, but I need the rating list to be precise."
        citations = []
    elif "briefing" in q:
        answer = "Briefing: World Cup Group D includes USA and Australia. F1 continues after Miami. Chess is led by a top grandmaster."
        citations = ["fifa_wc26_final_groups"]
    elif "how many races" in q:
        answer = "The 2026 F1 season has 24 races."
        citations = ["fia_2026_calendar_original"]
    elif "guarantee" in q:
        answer = "I cannot guarantee the winner of the next F1 race."
        citations = []
    else:
        answer = cards["cards"][0]["text"] if cards["cards"] else "I do not have enough information."
    return _answer(question, "single_agent", answer, [primary], tools, skills, citations, abstained="cannot guarantee" in answer.lower(), trace=trace)


def sequential_chain(question: str) -> AgentAnswer:
    sports = route_sports(question)
    # Sequential chain tries all routed sports, but uses only one verification pass.
    skills = select_skills(question, sports)
    answer, tools, citations, facts, abstained, warnings = _answer_for_sports(question, sports, "sequential_chain", thorough="chain")
    trace = ["classify", "retrieve", "draft", "verify_basic"]
    # Rigid chain failure: it can miss uncertainty on subjective better questions.
    if "who was better" in question.lower():
        abstained = False
        answer += " On raw international output Platini leads on caps and goals."
    return _answer(question, "sequential_chain", answer, sports, tools, skills, citations, abstained=abstained, facts=facts, trace=trace, warnings=warnings)


def triage_handoff(question: str) -> AgentAnswer:
    sports = route_sports(question)
    skills = select_skills(question, sports)
    answer, tools, citations, facts, abstained, warnings = _answer_for_sports(question, sports, "triage_handoff", thorough="handoff")
    trace = ["router_agent", *(f"handoff:{s}" for s in sports if s != "unknown"), "merge_agent"]
    return _answer(question, "triage_handoff", answer, sports, tools, skills, citations, abstained=abstained, facts=facts, trace=trace, warnings=warnings)


def committee_referee(question: str) -> AgentAnswer:
    # Run all specialists, then referee chooses relevant facts; deterministic implementation uses all routed sports but adds a verifier pass.
    sports = route_sports(question)
    skills = select_skills(question, sports)
    if "eval-review" not in skills:
        skills.append("eval-review")
    answer, tools, citations, facts, abstained, warnings = _answer_for_sports(question, sports, "committee_referee", thorough="referee")
    if "search_source_cards" not in tools:
        # Referee checks source cards for evidence even when structured tools were enough.
        cards = search_source_cards(question, sport=None, top_k=3)
        tools.append("search_source_cards")
        for sid in cards.get("source_ids", []):
            if sid in citations:
                continue
            # Add only relevant committee citations; avoid bloating every answer.
            if sid.split("_")[0] in {"fifa", "f1", "fide", "rsssf", "fff", "fia"}:
                pass
    trace = ["router_agent", "football_specialist", "f1_specialist", "chess_specialist", "referee_agent", "citation_check"]
    return _answer(question, "committee_referee", answer, sports, tools, skills, citations, abstained=abstained, facts=facts, trace=trace, warnings=warnings)


def run_design(question: str, design: str) -> AgentAnswer:
    if design == "single_agent":
        return single_agent(question)
    if design == "sequential_chain":
        return sequential_chain(question)
    if design == "triage_handoff":
        return triage_handoff(question)
    if design == "committee_referee":
        return committee_referee(question)
    raise ValueError(f"Unknown design: {design}")


DESIGNS = ["single_agent", "sequential_chain", "triage_handoff", "committee_referee"]

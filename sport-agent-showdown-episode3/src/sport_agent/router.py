from __future__ import annotations

import re

SPORT_KEYWORDS = {
    "football": [
        "football", "soccer", "world cup", "fifa", "argentina", "italy", "group", "cruyff", "platini", "netherlands", "france", "messi", "mbappe", "socceroos", "australia", "usa", "paraguay", "turkiye", "türkiye"
    ],
    "f1": [
        "f1", "formula 1", "formula one", "grand prix", "verstappen", "mclaren", "ferrari", "red bull", "mercedes", "miami", "canada", "race", "driver", "lineup", "line-up"
    ],
    "chess": [
        "chess", "fide", "carlsen", "gukesh", "nakamura", "caruana", "rating", "classical", "grandmaster"
    ],
}


def route_sports(question: str) -> list[str]:
    q = question.lower()
    sports: list[str] = []
    for sport, keywords in SPORT_KEYWORDS.items():
        if any(k in q for k in keywords):
            sports.append(sport)
    if not sports:
        sports.append("unknown")
    return sports


def is_prediction_or_subjective(question: str) -> bool:
    q = question.lower()
    prediction_markers = ["guarantee", "predict", "who will win", "who won the 2026 fifa world cup", "better", "best ever", "objectively"]
    return any(m in q for m in prediction_markers)


def needs_mixed_skill(question: str) -> bool:
    sports = [s for s in route_sports(question) if s != "unknown"]
    return len(sports) > 1 or bool(re.search(r"briefing|compare|which is larger|and which|and the", question, re.I))

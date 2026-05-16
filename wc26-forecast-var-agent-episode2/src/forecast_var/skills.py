from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = PROJECT_ROOT / ".agents" / "skills"


def select_skills(question: str) -> list[str]:
    q = question.lower()
    skills: list[str] = ["forecast-preflight", "citation-discipline"]
    if any(w in q for w in ["source", "field", "group", "rank", "forecast", "predict", "favourite", "favorite", "win", "probability", "include", "outside", "ignore", "citation", "unsupported", "evidence", "final"]):
        skills.append("source-triage")
    if any(w in q for w in ["predict", "forecast", "probability", "favourite", "favorite", "win", "vs", "group", "top", "rank", "final"]):
        skills.append("forecast-modeling")
    if any(w in q for w in ["predict", "forecast", "probability", "certain", "guarantee", "definitely", "will win", "favourite", "favorite", "cannot know", "unsupported", "final"]):
        skills.append("uncertainty-calibration")
    if any(w in q for w in ["what if", "injury", "injuries", "suspended", "without", "scenario", "rating points", "loses"]):
        skills.append("scenario-analysis")
    return list(dict.fromkeys(skills))


@lru_cache(maxsize=None)
def read_skill(name: str) -> str:
    path = SKILLS_ROOT / name / "SKILL.md"
    return path.read_text(encoding="utf-8")


def build_skill_context(names: list[str]) -> str:
    return "\n\n".join(read_skill(name) for name in names)

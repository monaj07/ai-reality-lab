from __future__ import annotations

from pathlib import Path

from .router import is_prediction_or_subjective, needs_mixed_skill, route_sports

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / ".agents" / "skills"


def load_skill(name: str) -> str:
    path = SKILLS_DIR / name / "SKILL.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def select_skills(question: str, sports: list[str] | None = None) -> list[str]:
    sports = sports or route_sports(question)
    selected: list[str] = []
    if "football" in sports:
        selected.append("football-research")
    if "f1" in sports:
        selected.append("f1-research")
    if "chess" in sports:
        selected.append("chess-research")
    if needs_mixed_skill(question):
        selected.append("mixed-question-decomposition")
    if is_prediction_or_subjective(question):
        selected.append("uncertainty-calibration")
    selected.append("citation-discipline")
    # Preserve order, remove duplicates.
    out: list[str] = []
    for s in selected:
        if s not in out:
            out.append(s)
    return out

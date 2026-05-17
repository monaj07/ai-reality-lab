from __future__ import annotations

from functools import lru_cache
from pathlib import Path


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return YAML-like SKILL.md metadata and body without requiring PyYAML.

    The agent skills in this repo use simple frontmatter with exactly
    `name` and `description`. A small parser keeps the project lightweight.
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw_meta = text[4:end].strip().splitlines()
    metadata: dict[str, str] = {}
    for line in raw_meta:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, text[end + len("\n---\n"):].lstrip()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = PROJECT_ROOT / ".agents" / "skills"


def select_skills(question: str) -> list[str]:
    q = question.lower()
    skills: list[str] = ["forecast-preflight", "citation-discipline"]
    if any(w in q for w in ["source", "coverage", "field", "group", "rank", "forecast", "predict", "favourite", "favorite", "win", "probability", "include", "outside", "ignore", "citation", "unsupported", "evidence", "final", "market", "odds", "adapter"]):
        skills.append("source-triage")
    if any(w in q for w in ["predict", "forecast", "probability", "favourite", "favorite", "win", "vs", "group", "top", "rank", "final", "market", "odds", "monte carlo", "simulate", "champion", "rolling"]):
        skills.append("forecast-modeling")
    if any(w in q for w in ["predict", "forecast", "probability", "certain", "guarantee", "definitely", "will win", "favourite", "favorite", "cannot know", "unsupported", "final", "monte carlo", "simulate", "simulation", "champion", "rolling", "market", "odds"]):
        skills.append("uncertainty-calibration")
    if any(w in q for w in ["what if", "injury", "injuries", "suspended", "without", "scenario", "rating points", "loses", "rolling", "after"]):
        skills.append("scenario-analysis")
    if any(w in q for w in ["market", "odds", "coverage", "adapter", "source", "refresh"]):
        skills.append("source-adapter-governance")
    if any(w in q for w in ["monte carlo", "simulate", "simulation", "champion", "rolling", "after"]):
        skills.append("monte-carlo-forecasting")
    return list(dict.fromkeys(skills))


@lru_cache(maxsize=None)
def read_skill(name: str) -> str:
    path = SKILLS_ROOT / name / "SKILL.md"
    return path.read_text(encoding="utf-8")


def read_skill_metadata(name: str) -> dict[str, str]:
    """Read the `name` and `description` frontmatter for a skill."""
    metadata, _ = _parse_frontmatter(read_skill(name))
    return metadata


def build_skill_context(names: list[str]) -> str:
    """Build compact context for the selected procedural skills.

    The metadata remains visible to the model because it explains what each
    skill is for; the body carries the concrete procedure.
    """
    blocks: list[str] = []
    for name in names:
        raw = read_skill(name)
        metadata, body = _parse_frontmatter(raw)
        title = metadata.get("name", name)
        description = metadata.get("description", "")
        blocks.append(f"## Skill: {title}\nDescription: {description}\n\n{body}".strip())
    return "\n\n".join(blocks)

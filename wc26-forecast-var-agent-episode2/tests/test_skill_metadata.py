from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"


def _frontmatter(text: str) -> dict[str, str]:
    """Parse the tiny YAML frontmatter shape used by project skill cards.

    We intentionally avoid a YAML dependency because the skill metadata only
    allows simple `name: ...` and `description: ...` lines.
    """
    assert text.startswith("---\n"), "skill must start with YAML frontmatter"
    _, raw, _body = text.split("---", 2)
    meta: dict[str, str] = {}
    for line in raw.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta


def test_all_skills_have_name_and_description_frontmatter() -> None:
    for skill_dir in sorted(p for p in SKILLS_ROOT.iterdir() if p.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"missing SKILL.md for {skill_dir.name}"
        meta = _frontmatter(skill_file.read_text(encoding="utf-8"))
        assert set(meta) == {"name", "description"}
        assert meta["name"] == skill_dir.name
        assert meta["description"]
        assert meta["name"] == meta["name"].lower()

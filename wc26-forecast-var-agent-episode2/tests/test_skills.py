from pathlib import Path

from forecast_var.skills import read_skill_metadata, select_skills


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PROJECT_ROOT / ".agents" / "skills"


def test_all_agent_skills_have_frontmatter():
    skill_names = sorted(path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md"))
    assert skill_names
    for skill_name in skill_names:
        metadata = read_skill_metadata(skill_name)
        assert metadata["name"] == skill_name
        assert metadata["description"]
        assert len(metadata["description"].split()) >= 12


def test_skill_router_still_selects_monte_carlo_skill():
    selected = select_skills("Run a Monte Carlo tournament simulation")
    assert "forecast-preflight" in selected
    assert "monte-carlo-forecasting" in selected

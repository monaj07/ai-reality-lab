from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp.server.fastmcp import FastMCP
from forecast_var import tools

mcp = FastMCP("worldcup_forecast", json_response=True)


@mcp.tool()
def validate_tournament_field() -> dict:
    """Validate the 48-team 2026 World Cup field and whether Italy is present."""
    return tools.validate_tournament_field()


@mcp.tool()
def get_source_registry() -> dict:
    """Return active, placeholder, and disabled forecasting sources."""
    return tools.get_source_registry()


@mcp.tool()
def list_groups() -> dict:
    """Return 2026 World Cup groups."""
    return tools.list_groups()


@mcp.tool()
def get_team_inputs(team: str) -> dict:
    """Return bundled demo feature inputs for one qualified team."""
    return tools.get_team_inputs(team)


@mcp.tool()
def forecast_match(team_a: str, team_b: str, adjustments: dict | None = None) -> dict:
    """Forecast one match using the demo model."""
    return tools.forecast_match(team_a, team_b, adjustments)


@mcp.tool()
def forecast_group(group: str, sims: int = 5000, adjustments: dict | None = None) -> dict:
    """Simulate one group using the demo model."""
    return tools.forecast_group(group, sims=sims, adjustments=adjustments)


@mcp.tool()
def rank_teams(limit: int = 10, adjustments: dict | None = None) -> dict:
    """Return demo tournament favourite ranking."""
    return tools.rank_teams(limit=limit, adjustments=adjustments)


@mcp.tool()
def explain_model() -> dict:
    """Explain the forecasting model and limitations."""
    return tools.explain_model()


if __name__ == "__main__":
    mcp.run(transport="stdio")

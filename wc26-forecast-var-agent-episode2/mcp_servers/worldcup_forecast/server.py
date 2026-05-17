from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mcp.server.fastmcp import FastMCP
from forecast_var import tools

mcp = FastMCP("worldcup_forecast", json_response=True)


@mcp.tool()
def search_source_cards(query: str, k: int = 5) -> dict:
    """Retrieve local source cards for factual/model grounding."""
    return tools.search_source_cards(query, k=k)


@mcp.tool()
def preflight_forecast_context() -> dict:
    """Validate field, feature, and source readiness before forecasts."""
    return tools.preflight_forecast_context()


@mcp.tool()
def validate_tournament_field() -> dict:
    """Validate the 48-team 2026 World Cup field and groups."""
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


@mcp.tool()
def verify_claims_against_sources(claims: list[dict]) -> dict:
    """Classify answer claims as source-supported, model-derived, partial, or unsupported."""
    return tools.verify_claims_against_sources(claims)


# Source-aware Forecast VAR upgrades. These tools are deliberately read-only
# except for refresh_evidence_index, which writes a local generated JSONL index.

@mcp.tool()
def refresh_evidence_index(include_live_api: bool = False) -> dict:
    """Rebuild the local evidence index from bundled adapters; live API is opt-in."""
    return tools.refresh_evidence_index(include_live_api=include_live_api)


@mcp.tool()
def search_evidence_index(query: str, k: int = 8) -> dict:
    """Search the generated evidence index across source cards, team profiles, market rows, and curated notes."""
    return tools.search_evidence_index(query, k=k)


@mcp.tool()
def source_coverage_report() -> dict:
    """Return coverage status for official, demo, adapter, curated, and market sources."""
    return tools.source_coverage_report()


@mcp.tool()
def extract_market_baseline(team_a: str, team_b: str) -> dict:
    """Return de-vig sample market probabilities for a matchup when bundled demo odds exist."""
    return tools.extract_market_baseline(team_a, team_b)


@mcp.tool()
def forecast_match_with_context(team_a: str, team_b: str) -> dict:
    """Forecast a match with team features, evidence retrieval, sample market comparison, and data gaps."""
    return tools.forecast_match_with_context(team_a, team_b)


@mcp.tool()
def simulate_tournament(sims: int = 3000, seed: int = 2026, limit: int = 12) -> dict:
    """Run the approximate whole-tournament Monte Carlo simulator."""
    return tools.simulate_tournament(sims=sims, seed=seed, limit=limit)


@mcp.tool()
def rolling_group_forecast(group: str, completed_results: list[dict], sims: int = 5000) -> dict:
    """Forecast a group after locking user-supplied completed match results."""
    return tools.rolling_group_forecast(group, completed_results=completed_results, sims=sims)

if __name__ == "__main__":
    mcp.run(transport="stdio")

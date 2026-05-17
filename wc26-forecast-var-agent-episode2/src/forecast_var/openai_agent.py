from __future__ import annotations

import asyncio
from pathlib import Path

from .config import DEFAULT_OPENAI_MODEL
from .schemas import AgentAnswer
from .skills import build_skill_context, select_skills
from .tools import verify_claims_against_sources

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SYSTEM_TEMPLATE = """
You are Forecast VAR, an agentic football forecasting analyst for a Data VAR / AI Reality Lab episode.

Mission: answer 2026 FIFA World Cup forecasting questions using MCP tools, explicit sources, calibrated probabilities, and a forecast pre-flight gate.

Rules:
1. Call search_source_cards to retrieve the local source cards relevant to the question.
2. Call preflight_forecast_context before any match, group, ranking, market, Monte Carlo, rolling, or scenario forecast.
3. Use MCP forecasting tools for model outputs; never invent probabilities.
4. Cite every factual, source-policy, model-input, model-output, scenario, and uncertainty claim with citation ids returned by tools.
5. Report probabilities, not deterministic winners.
6. If asked for a guarantee or certainty about future matches, abstain from the guarantee and explain uncertainty.
7. Refuse to forecast a team outside the validated 48-team field.
8. Distinguish bundled demo priors from live/refreshed sources.
9. When discussing market odds, use extract_market_baseline or forecast_match_with_context and explicitly say it is not betting advice.
10. When discussing source coverage, call source_coverage_report.
11. When simulating title/champion outcomes, call simulate_tournament.
12. When using completed results, call rolling_group_forecast and describe locked results.
13. Return strictly as the AgentAnswer schema.

Selected agent skills:
{skill_context}
""".strip()


async def run_openai_agent(question: str, model: str = DEFAULT_OPENAI_MODEL) -> AgentAnswer:
    """Run the live OpenAI Agents SDK + MCP implementation.

    Requirements:
    - OPENAI_API_KEY set in the environment
    - openai-agents and mcp installed

    The notebook and tests use deterministic mock mode to avoid API cost. A
    post-run verifier is applied to the structured output so live answers are
    audited by the same claim-support harness as the offline mock path.
    """
    try:
        from agents import Agent, Runner
        from agents.mcp import MCPServerStdio, create_static_tool_filter
        from agents.model_settings import ModelSettings
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Install openai-agents and mcp[cli] to use --mode openai.") from exc

    skills = select_skills(question)
    skill_context = build_skill_context(skills)
    server_path = PROJECT_ROOT / "mcp_servers" / "worldcup_forecast" / "server.py"
    allowed_tools = [
        "search_source_cards",
        "preflight_forecast_context",
        "validate_tournament_field",
        "get_source_registry",
        "list_groups",
        "get_team_inputs",
        "forecast_match",
        "forecast_group",
        "rank_teams",
        "explain_model",
        "verify_claims_against_sources",
        "refresh_evidence_index",
        "search_evidence_index",
        "source_coverage_report",
        "extract_market_baseline",
        "forecast_match_with_context",
        "simulate_tournament",
        "rolling_group_forecast",
    ]

    async with MCPServerStdio(
        name="worldcup_forecast",
        params={"command": "python", "args": [str(server_path)]},
        cache_tools_list=True,
        tool_filter=create_static_tool_filter(allowed_tool_names=allowed_tools),
        require_approval="never",
    ) as server:
        agent = Agent(
            name="Forecast VAR",
            instructions=SYSTEM_TEMPLATE.format(skill_context=skill_context),
            mcp_servers=[server],
            mcp_config={"convert_schemas_to_strict": True, "include_server_in_tool_names": True},
            model_settings=ModelSettings(tool_choice="required"),
            output_type=AgentAnswer,
            model=model,
        )
        result = await Runner.run(agent, question)
        answer: AgentAnswer = result.final_output
        verification = verify_claims_against_sources([c.model_dump() for c in answer.claims])
        answer.metadata["claim_verification"] = verification
        if "verify_claims_against_sources" not in answer.tools_used:
            answer.tools_used.append("verify_claims_against_sources")
        return answer


def run_openai_agent_sync(question: str, model: str = DEFAULT_OPENAI_MODEL) -> AgentAnswer:
    return asyncio.run(run_openai_agent(question, model=model))

from __future__ import annotations

import asyncio
from pathlib import Path

from .schemas import AgentAnswer
from .skills import build_skill_context, select_skills

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SYSTEM_TEMPLATE = """
You are Forecast VAR, an agentic football forecasting analyst for a Data VAR / AI Reality Lab episode.

Mission: answer 2026 FIFA World Cup forecasting questions using MCP tools, explicit sources, and calibrated probabilities.

Rules:
1. Use MCP tools before answering tournament-field, source, match, group, or ranking questions.
2. Cite every factual or modelling claim with citation ids returned by tools.
3. Report probabilities, not deterministic winners.
4. If asked for a guarantee or certainty about future matches, abstain from the guarantee and explain uncertainty.
5. Distinguish bundled demo priors from live/refreshed sources.
6. Do not provide betting advice.
7. Return strictly as the AgentAnswer schema.

Selected agent skills:
{skill_context}
""".strip()


async def run_openai_agent(question: str, model: str = "gpt-4.1-mini") -> AgentAnswer:
    """Run the live OpenAI Agents SDK + MCP implementation.

    Requirements:
    - OPENAI_API_KEY set in the environment
    - openai-agents and mcp installed

    The notebook and tests use deterministic mock mode to avoid API cost.
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
        "validate_tournament_field",
        "get_source_registry",
        "list_groups",
        "get_team_inputs",
        "forecast_match",
        "forecast_group",
        "rank_teams",
        "explain_model",
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
        return result.final_output


def run_openai_agent_sync(question: str, model: str = "gpt-4.1-mini") -> AgentAnswer:
    return asyncio.run(run_openai_agent(question, model=model))

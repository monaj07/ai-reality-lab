from __future__ import annotations

import asyncio
from pathlib import Path

from pydantic import BaseModel, Field

from .skills import load_skill

ROOT = Path(__file__).resolve().parents[2]
MCP_SERVER = ROOT / "mcp_servers" / "sport_knowledge" / "server.py"


class LiveSportAnswer(BaseModel):
    answer: str = Field(description="User-facing answer with concise source references.")
    sports: list[str]
    tools_used: list[str]
    skills_used: list[str]
    citations: list[str]
    abstained: bool = False
    uncertainty_notes: list[str] = []


BASE_INSTRUCTIONS = """
You are Sport Agent, a source-grounded multi-sport assistant for football, Formula 1 and chess.
Use MCP tools before answering factual questions.
Return only structured output matching the schema.
Every factual claim must cite source_id values returned by tools.
Do not guarantee future sporting results.
"""


def _skill_block(names: list[str]) -> str:
    return "\n\n".join(load_skill(n) for n in names)


async def run_openai_triage(question: str, model: str = "gpt-4.1-mini") -> LiveSportAnswer:
    """Run a live triage-handoff design using OpenAI Agents SDK and the local MCP server.

    This function is optional. Offline scripts use deterministic mock designs.
    """
    try:
        from agents import Agent, Runner
        from agents.mcp import MCPServerStdio, create_static_tool_filter
        from agents.model_settings import ModelSettings
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install openai-agents and set OPENAI_API_KEY to use live mode.") from exc

    allowed_tools = [
        "route_sport",
        "search_source_cards",
        "get_world_cup_group",
        "get_f1_calendar",
        "get_f1_driver_lineup",
        "get_chess_top_players",
        "compare_legacy_football_players",
    ]
    async with MCPServerStdio(
        name="sport_knowledge",
        params={"command": "python", "args": [str(MCP_SERVER)]},
        cache_tools_list=True,
        tool_filter=create_static_tool_filter(allowed_tool_names=allowed_tools),
    ) as server:
        football = Agent(
            name="Football specialist",
            instructions=BASE_INSTRUCTIONS + "\n" + _skill_block(["football-research", "citation-discipline", "uncertainty-calibration"]),
            mcp_servers=[server],
            output_type=LiveSportAnswer,
            model=model,
            model_settings=ModelSettings(tool_choice="required"),
        )
        f1 = Agent(
            name="F1 specialist",
            instructions=BASE_INSTRUCTIONS + "\n" + _skill_block(["f1-research", "citation-discipline", "uncertainty-calibration"]),
            mcp_servers=[server],
            output_type=LiveSportAnswer,
            model=model,
            model_settings=ModelSettings(tool_choice="required"),
        )
        chess = Agent(
            name="Chess specialist",
            instructions=BASE_INSTRUCTIONS + "\n" + _skill_block(["chess-research", "citation-discipline"]),
            mcp_servers=[server],
            output_type=LiveSportAnswer,
            model=model,
            model_settings=ModelSettings(tool_choice="required"),
        )
        router = Agent(
            name="Sport triage router",
            instructions=(
                BASE_INSTRUCTIONS
                + "\nDecide whether to answer directly or hand off to the relevant specialist. "
                + "Use mixed-question-decomposition when the question spans sports."
                + "\n"
                + _skill_block(["mixed-question-decomposition", "citation-discipline"])
            ),
            handoffs=[football, f1, chess],
            mcp_servers=[server],
            output_type=LiveSportAnswer,
            model=model,
            model_settings=ModelSettings(tool_choice="required"),
        )
        result = await Runner.run(router, question)
        output = result.final_output
        if isinstance(output, LiveSportAnswer):
            return output
        return LiveSportAnswer.model_validate(output)


def run_openai_triage_sync(question: str, model: str = "gpt-4.1-mini") -> LiveSportAnswer:
    return asyncio.run(run_openai_triage(question, model=model))

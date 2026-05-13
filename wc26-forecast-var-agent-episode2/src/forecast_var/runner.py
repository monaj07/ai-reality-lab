from __future__ import annotations

from .mock_agent import run_baseline_mock, run_grounded_mock


def run_agent(question: str, mode: str = "grounded_mock", model: str = "gpt-4.1-mini"):
    if mode == "baseline_mock":
        return run_baseline_mock(question)
    if mode == "grounded_mock":
        return run_grounded_mock(question)
    if mode == "openai":
        from .openai_agent import run_openai_agent_sync
        return run_openai_agent_sync(question, model=model)
    raise ValueError(f"Unknown mode: {mode}")

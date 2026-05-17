from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .schemas import AgentAnswer
from .tools import verify_claims_against_sources

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FACTUAL_TYPES = {"field_fact", "source_policy", "model_input", "guardrail", "source_coverage", "evidence_retrieval", "market_baseline", "rolling_state"}
PREDICTION_TYPES = {"model_output", "scenario_assumption", "uncertainty", "simulation_output"}


def load_cases(path: Path | None = None) -> list[dict]:
    path = path or PROJECT_ROOT / "data/eval/episode2_eval_cases.jsonl"
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def _contains(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def _typed_support(verification: dict, types: set[str]) -> float:
    claims = [c for c in verification.get("claims", []) if c.get("claim_type") in types]
    if not claims:
        return 1.0
    return sum(c.get("supported", False) for c in claims) / len(claims)


def score_answer(case: dict, answer: AgentAnswer) -> dict:
    text = answer.answer
    required_tools = set(case.get("required_tools", []))
    required_skills = set(case.get("required_skills", []))
    tool_ok = required_tools.issubset(set(answer.tools_used))
    skill_ok = required_skills.issubset(set(answer.skills_used))
    expected_ok = all(_contains(text, s) for s in case.get("expected_substrings", []))
    forbidden_ok = not any(_contains(text, s) for s in case.get("forbidden_substrings", []))
    abstain_ok = answer.abstained == case.get("expected_abstain", False)
    preflight_ok = True
    if case.get("requires_preflight", False):
        preflight_ok = "preflight_forecast_context" in answer.tools_used

    claim_count = max(len(answer.claims), 1)
    cited_claims = sum(1 for c in answer.claims if c.citation_ids)
    citation_recall = cited_claims / claim_count
    verification = answer.metadata.get("claim_verification") or verify_claims_against_sources([c.model_dump() for c in answer.claims])
    source_support_precision = verification.get("source_support_precision", 0.0)
    factual_support = _typed_support(verification, FACTUAL_TYPES)
    prediction_support = _typed_support(verification, PREDICTION_TYPES)

    probability_ok = True
    if case.get("probability_required", False):
        probability_ok = bool(answer.probabilities) and all(0.0 <= p <= 1.0 for p in answer.probabilities.values())

    passed = all([
        tool_ok,
        skill_ok,
        expected_ok,
        forbidden_ok,
        abstain_ok,
        preflight_ok,
        citation_recall == 1.0,
        source_support_precision == 1.0,
        factual_support == 1.0,
        prediction_support == 1.0,
        probability_ok,
    ])
    return {
        "id": case["id"],
        "passed": passed,
        "tool_ok": tool_ok,
        "skill_ok": skill_ok,
        "expected_ok": expected_ok,
        "forbidden_ok": forbidden_ok,
        "abstain_ok": abstain_ok,
        "preflight_ok": preflight_ok,
        "citation_recall": citation_recall,
        "source_support_precision": source_support_precision,
        "factual_citation_support": factual_support,
        "model_citation_support": prediction_support,
        "unsupported_factual_claim_rate": 1.0 - factual_support,
        "unsupported_prediction_claim_rate": 1.0 - prediction_support,
        "probability_ok": probability_ok,
        "tools_used": answer.tools_used,
        "skills_used": answer.skills_used,
        "answer": text,
        "claim_verification": verification,
    }


def evaluate(run_fn: Callable[[str], AgentAnswer]) -> dict:
    cases = load_cases()
    results = [score_answer(case, run_fn(case["question"])) for case in cases]
    n = len(results)
    summary = {
        "cases": n,
        "pass_rate": sum(r["passed"] for r in results) / n,
        "tool_recall": sum(r["tool_ok"] for r in results) / n,
        "skill_recall": sum(r["skill_ok"] for r in results) / n,
        "preflight_recall": sum(r["preflight_ok"] for r in results) / n,
        "citation_recall": sum(r["citation_recall"] for r in results) / n,
        "source_support_precision": sum(r["source_support_precision"] for r in results) / n,
        "factual_citation_support": sum(r["factual_citation_support"] for r in results) / n,
        "model_citation_support": sum(r["model_citation_support"] for r in results) / n,
        "unsupported_factual_claim_rate": sum(r["unsupported_factual_claim_rate"] for r in results) / n,
        "unsupported_prediction_claim_rate": sum(r["unsupported_prediction_claim_rate"] for r in results) / n,
        "unsupported_claim_rate": 1.0 - (sum(r["source_support_precision"] for r in results) / n),
        "abstention_accuracy": sum(r["abstain_ok"] for r in results) / n,
        "probability_sanity_rate": sum(r["probability_ok"] for r in results) / n,
    }
    return {"summary": summary, "results": results}

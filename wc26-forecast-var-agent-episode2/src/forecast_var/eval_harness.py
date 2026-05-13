from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .schemas import AgentAnswer

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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


def score_answer(case: dict, answer: AgentAnswer) -> dict:
    text = answer.answer
    required_tools = set(case.get("required_tools", []))
    required_skills = set(case.get("required_skills", []))
    tool_ok = required_tools.issubset(set(answer.tools_used))
    skill_ok = required_skills.issubset(set(answer.skills_used))
    expected_ok = all(_contains(text, s) for s in case.get("expected_substrings", []))
    forbidden_ok = not any(_contains(text, s) for s in case.get("forbidden_substrings", []))
    abstain_ok = answer.abstained == case.get("expected_abstain", False)
    claim_count = max(len(answer.claims), 1)
    cited_claims = sum(1 for c in answer.claims if c.citation_ids)
    citation_recall = cited_claims / claim_count
    probability_ok = True
    if case.get("probability_required", False):
        probability_ok = bool(answer.probabilities) and all(0.0 <= p <= 1.0 for p in answer.probabilities.values())
    passed = all([tool_ok, skill_ok, expected_ok, forbidden_ok, abstain_ok, citation_recall == 1.0, probability_ok])
    return {
        "id": case["id"],
        "passed": passed,
        "tool_ok": tool_ok,
        "skill_ok": skill_ok,
        "expected_ok": expected_ok,
        "forbidden_ok": forbidden_ok,
        "abstain_ok": abstain_ok,
        "citation_recall": citation_recall,
        "probability_ok": probability_ok,
        "tools_used": answer.tools_used,
        "skills_used": answer.skills_used,
        "answer": text,
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
        "citation_recall": sum(r["citation_recall"] for r in results) / n,
        "unsupported_claim_rate": 1.0 - (sum(r["citation_recall"] for r in results) / n),
        "abstention_accuracy": sum(r["abstain_ok"] for r in results) / n,
        "probability_sanity_rate": sum(r["probability_ok"] for r in results) / n,
    }
    return {"summary": summary, "results": results}

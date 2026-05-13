from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Iterable

from .data import DATA, load_jsonl
from .designs import DESIGNS, run_design
from .schemas import AgentAnswer, EvalCase, EvalResult


def _recall(required: list[str], observed: list[str]) -> float:
    if not required:
        return 1.0
    observed_set = set(observed)
    return sum(1 for x in required if x in observed_set) / len(required)


def _keyword_recall(keywords: list[str], text: str) -> float:
    if not keywords:
        return 1.0
    t = text.lower()
    return sum(1 for k in keywords if k.lower() in t) / len(keywords)


def _forbidden_absence(forbidden: list[str], text: str) -> float:
    if not forbidden:
        return 1.0
    t = text.lower()
    return 1.0 if all(f.lower() not in t for f in forbidden) else 0.0


def load_eval_cases(path: str | Path | None = None) -> list[EvalCase]:
    path = Path(path) if path else DATA / "eval" / "episode3_eval_cases.jsonl"
    return [EvalCase(**row) for row in load_jsonl(path)]


def evaluate_answer(case: EvalCase, answer: AgentAnswer) -> EvalResult:
    route_accuracy = _recall(case.expected_sports, answer.sports)
    tool_recall = _recall(case.required_tools, answer.tools_used)
    skill_recall = _recall(case.required_skills, answer.skills_used)
    citation_recall = _recall(case.required_citations, answer.citations)
    keyword_recall = _keyword_recall(case.expected_keywords, answer.answer)
    forbidden_absence = _forbidden_absence(case.forbidden_keywords, answer.answer)
    abstention_accuracy = 1.0 if answer.abstained == case.should_abstain else 0.0

    failures: list[str] = []
    checks = {
        "route_accuracy": route_accuracy,
        "tool_recall": tool_recall,
        "skill_recall": skill_recall,
        "citation_recall": citation_recall,
        "keyword_recall": keyword_recall,
        "forbidden_absence": forbidden_absence,
        "abstention_accuracy": abstention_accuracy,
    }
    for name, val in checks.items():
        if val < 1.0:
            failures.append(name)

    unsupported_claim = citation_recall < 1.0 or forbidden_absence < 1.0 or keyword_recall < 0.6
    passed = not failures
    return EvalResult(
        case_id=case.case_id,
        question=case.question,
        design=answer.design,
        passed=passed,
        route_accuracy=route_accuracy,
        tool_recall=tool_recall,
        skill_recall=skill_recall,
        citation_recall=citation_recall,
        keyword_recall=keyword_recall,
        forbidden_absence=forbidden_absence,
        abstention_accuracy=abstention_accuracy,
        unsupported_claim=unsupported_claim,
        tool_calls=len(answer.tools_used),
        cost_proxy=answer.cost_proxy,
        answer=answer,
        failures=failures,
    )


def evaluate_design(design: str, cases: Iterable[EvalCase] | None = None) -> list[EvalResult]:
    cases = list(cases or load_eval_cases())
    results = []
    for case in cases:
        answer = run_design(case.question, design)
        results.append(evaluate_answer(case, answer))
    return results


def summarise(results: list[EvalResult]) -> dict[str, float | int | str]:
    if not results:
        return {}
    return {
        "design": results[0].design,
        "cases": len(results),
        "pass_rate": mean(1.0 if r.passed else 0.0 for r in results),
        "route_accuracy": mean(r.route_accuracy for r in results),
        "tool_recall": mean(r.tool_recall for r in results),
        "skill_recall": mean(r.skill_recall for r in results),
        "citation_recall": mean(r.citation_recall for r in results),
        "keyword_recall": mean(r.keyword_recall for r in results),
        "forbidden_absence": mean(r.forbidden_absence for r in results),
        "abstention_accuracy": mean(r.abstention_accuracy for r in results),
        "unsupported_claim_rate": mean(1.0 if r.unsupported_claim else 0.0 for r in results),
        "avg_tool_calls": mean(r.tool_calls for r in results),
        "avg_cost_proxy": mean(r.cost_proxy for r in results),
    }


def write_results(results: list[EvalResult], out_dir: str | Path = "reports") -> dict[str, float | int | str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    design = results[0].design if results else "unknown"
    jsonl_path = out / f"eval_{design}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(r.model_dump_json() + "\n")
    summary = summarise(results)
    (out / f"summary_{design}.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def evaluate_all(out_dir: str | Path = "reports") -> list[dict[str, float | int | str]]:
    summaries = []
    cases = load_eval_cases()
    for design in DESIGNS:
        results = evaluate_design(design, cases)
        summaries.append(write_results(results, out_dir))
    return summaries

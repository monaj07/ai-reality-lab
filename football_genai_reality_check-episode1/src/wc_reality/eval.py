from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean
from typing import Iterable

from .facts import FactStore, default_eval_path, load_jsonl
from .guardrails import extract_citation_ids, is_abstention, unsupported_sentences


def load_eval_cases(path: str | Path | None = None) -> list[dict]:
    return load_jsonl(path or default_eval_path())


def _contains(text: str, phrase: str) -> bool:
    return phrase.lower().replace("-", " ") in text.lower().replace("-", " ")


def score_answer(answer_obj: dict, case: dict, store: FactStore) -> dict:
    answer_text = answer_obj.get("answer", "")
    cited_ids = set(extract_citation_ids(answer_text))
    cited_ids.update(c.get("fact_id", "") for c in answer_obj.get("citations", []) if c.get("fact_id"))
    valid_cited_ids = {fid for fid in cited_ids if store.get(fid)}
    gold_ids = set(case.get("gold_support_ids", []))
    should_abstain = bool(case.get("should_abstain", False))
    abstained = bool(answer_obj.get("abstained", False)) or is_abstention(answer_text)

    if gold_ids:
        citation_recall = len(valid_cited_ids & gold_ids) / len(gold_ids)
        citation_precision = len(valid_cited_ids & gold_ids) / max(len(valid_cited_ids), 1)
    else:
        citation_recall = 1.0 if not valid_cited_ids else 0.0
        citation_precision = 1.0 if not valid_cited_ids else 0.0

    must_mention = case.get("must_mention", [])
    mention_recall = (
        sum(_contains(answer_text, phrase) for phrase in must_mention) / len(must_mention)
        if must_mention
        else 1.0
    )
    unsupported = unsupported_sentences(answer_text, store.by_id.keys())
    sentences = [s for s in answer_text.split(".") if s.strip()]
    unsupported_rate = len(unsupported) / max(len(sentences), 1)
    abstention_correct = abstained if should_abstain else not abstained

    required_mention_recall = 1.0 if case.get("category") == "answerable_all_48_teams" else 0.5
    if should_abstain:
        passed = abstention_correct and citation_precision >= 0.8 and "Brazil will host" not in answer_text
    else:
        passed = (
            abstention_correct
            and citation_recall >= 0.8
            and citation_precision >= 0.8
            and mention_recall >= required_mention_recall
            and unsupported_rate <= 0.25
        )

    return {
        "case_id": case["id"],
        "category": case.get("category", "unknown"),
        "question": case["question"],
        "answer": answer_text,
        "agent_abstained": abstained,
        "should_abstain": should_abstain,
        "cited_ids": ",".join(sorted(valid_cited_ids)),
        "gold_support_ids": ",".join(sorted(gold_ids)),
        "citation_precision": round(citation_precision, 3),
        "citation_recall": round(citation_recall, 3),
        "must_mention_recall": round(mention_recall, 3),
        "unsupported_rate": round(unsupported_rate, 3),
        "abstention_correct": abstention_correct,
        "passed": passed,
        "unsupported_sentences": " | ".join(unsupported),
    }


def summarize(rows: Iterable[dict]) -> dict:
    rows = list(rows)
    if not rows:
        return {}
    return {
        "citation_precision": round(mean(float(r["citation_precision"]) for r in rows), 3),
        "citation_recall": round(mean(float(r["citation_recall"]) for r in rows), 3),
        "must_mention_recall": round(mean(float(r["must_mention_recall"]) for r in rows), 3),
        "unsupported_rate": round(mean(float(r["unsupported_rate"]) for r in rows), 3),
        "pass_rate": round(mean(1.0 if r["passed"] else 0.0 for r in rows), 3),
        "abstention_accuracy": round(mean(1.0 if r["abstention_correct"] else 0.0 for r in rows), 3),
        "n_cases": len(rows),
    }


def write_outputs(rows: list[dict], summary: dict, out_dir: str | Path, agent_name: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if rows:
        with (out / f"{agent_name}_eval_results.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    (out / f"{agent_name}_eval_results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (out / f"{agent_name}_metric_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [f"# Evaluation summary: {agent_name}", ""]
    lines.extend(f"- **{k}**: {v}" for k, v in summary.items())
    lines.append("\n## Failed cases\n")
    for row in rows:
        if not row["passed"]:
            lines.append(f"### {row['case_id']}\n")
            lines.append(f"Question: {row['question']}\n")
            lines.append(f"Answer: {row['answer']}\n")
    (out / f"{agent_name}_eval_summary.md").write_text("\n".join(lines), encoding="utf-8")

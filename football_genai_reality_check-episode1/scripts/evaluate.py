#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from wc_reality.eval import load_eval_cases, score_answer, summarize, write_outputs
from wc_reality.facts import FactStore
from wc_reality.mock_agents import answer_baseline, answer_grounded
from wc_reality.openai_agent import answer_with_openai


def run_agent(name: str, backend: str, cases: list[dict], store: FactStore, model: str | None) -> tuple[list[dict], dict]:
    rows = []
    for case in cases:
        if name == "baseline":
            answer = answer_baseline(case["question"], store)
        elif backend == "openai":
            answer = answer_with_openai(case["question"], store, model=model)
        else:
            answer = answer_grounded(case["question"], store)
        row = score_answer(answer, case, store)
        row["agent"] = name
        rows.append(row)
    return rows, summarize(rows)


def plot_summary(all_rows: list[dict], out_dir: Path) -> None:
    image_dir = out_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(all_rows)
    if df.empty:
        return
    summary = df.groupby("agent")[
        ["citation_precision", "citation_recall", "must_mention_recall", "unsupported_rate", "passed", "abstention_correct"]
    ].mean().rename(columns={"passed": "pass_rate", "abstention_correct": "abstention_accuracy"})

    metrics = ["citation_precision", "citation_recall", "must_mention_recall", "pass_rate", "abstention_accuracy"]
    ax = summary[metrics].T.plot(kind="bar", figsize=(10, 5))
    ax.set_ylim(0, 1.05)
    ax.set_title("Agent quality metrics: baseline vs grounded")
    ax.set_ylabel("Score")
    ax.set_xlabel("Metric")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(image_dir / "metrics_bar.png", dpi=160)
    plt.close()

    pivot = df.pivot_table(index="case_id", columns="agent", values="passed", aggfunc="mean").fillna(0)
    fig, ax = plt.subplots(figsize=(6, max(4, 0.35 * len(pivot))))
    ax.imshow(pivot.values, aspect="auto")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_title("Pass/fail matrix by eval case")
    for y in range(len(pivot.index)):
        for x in range(len(pivot.columns)):
            ax.text(x, y, "PASS" if pivot.values[y, x] else "FAIL", ha="center", va="center")
    plt.tight_layout()
    plt.savefig(image_dir / "pass_fail_matrix.png", dpi=160)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate football AI agent grounding behavior.")
    parser.add_argument("--agent", choices=["baseline", "grounded", "both"], default="both")
    parser.add_argument("--backend", choices=["mock", "openai"], default="mock")
    parser.add_argument("--facts", default=None)
    parser.add_argument("--eval-set", default=None)
    parser.add_argument("--out-dir", default="reports")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    store = FactStore.from_jsonl(args.facts)
    cases = load_eval_cases(args.eval_set)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    agents = ["baseline", "grounded"] if args.agent == "both" else [args.agent]
    all_rows = []
    combined_summary = {}
    for agent_name in agents:
        rows, summary = run_agent(agent_name, args.backend, cases, store, args.model)
        write_outputs(rows, summary, out_dir, agent_name)
        all_rows.extend(rows)
        combined_summary[agent_name] = summary

    pd.DataFrame(all_rows).to_csv(out_dir / "combined_eval_results.csv", index=False)
    (out_dir / "combined_eval_results.json").write_text(json.dumps(all_rows, indent=2), encoding="utf-8")
    (out_dir / "combined_metric_summary.json").write_text(json.dumps(combined_summary, indent=2), encoding="utf-8")
    plot_summary(all_rows, out_dir)
    print(json.dumps(combined_summary, indent=2))


if __name__ == "__main__":
    main()

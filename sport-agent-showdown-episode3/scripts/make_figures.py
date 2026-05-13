from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    reports = Path("reports")
    if not (reports / "summary_all_designs.csv").exists():
        raise SystemExit("Run scripts/evaluate.py --design all first.")
    figs = reports / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(reports / "summary_all_designs.csv")

    plt.figure(figsize=(9, 5))
    plt.bar(df["design"], df["pass_rate"])
    plt.ylim(0, 1.05)
    plt.ylabel("Pass rate")
    plt.title("Agent design comparison on mixed sport evals")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(figs / "design_pass_rate.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.scatter(df["avg_cost_proxy"], df["pass_rate"], s=120)
    for _, row in df.iterrows():
        plt.annotate(row["design"], (row["avg_cost_proxy"], row["pass_rate"]), xytext=(5, 5), textcoords="offset points")
    plt.xlabel("Average cost proxy")
    plt.ylabel("Pass rate")
    plt.ylim(0, 1.05)
    plt.title("Quality/cost trade-off")
    plt.tight_layout()
    plt.savefig(figs / "tool_cost_tradeoff.png", dpi=160)
    plt.close()

    metrics = ["route_accuracy", "tool_recall", "skill_recall", "citation_recall", "abstention_accuracy"]
    x = range(len(metrics))
    plt.figure(figsize=(10, 5))
    for _, row in df.iterrows():
        plt.plot(list(x), [row[m] for m in metrics], marker="o", label=row["design"])
    plt.xticks(list(x), metrics, rotation=25, ha="right")
    plt.ylim(0, 1.05)
    plt.ylabel("Score")
    plt.title("Design metric profile")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figs / "metric_radar_like.png", dpi=160)
    plt.close()

    print(json.dumps({"figures": [str(p) for p in sorted(figs.glob("*.png"))]}, indent=2))


if __name__ == "__main__":
    main()

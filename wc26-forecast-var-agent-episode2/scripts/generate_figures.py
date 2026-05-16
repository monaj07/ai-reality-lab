from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt

from forecast_var.tools import forecast_group, rank_teams, preflight_forecast_context

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIG = PROJECT_ROOT / "figures"
FIG.mkdir(exist_ok=True)


def save_group_d() -> None:
    res = forecast_group("D")
    teams = list(res["group_probabilities"].keys())
    vals = [res["group_probabilities"][t]["winner"] for t in teams]
    plt.figure(figsize=(8, 4.5))
    plt.bar(teams, vals)
    plt.ylabel("Group winner probability")
    plt.title("Forecast VAR demo: Group D winner probabilities")
    plt.ylim(0, max(vals) * 1.25)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(FIG / "group_d_winner_probabilities.png", dpi=160)
    plt.close()


def save_top_favourites() -> None:
    res = rank_teams(10)
    teams = [r["team"] for r in res["ranked"]]
    vals = [r["demo_title_probability"] for r in res["ranked"]]
    plt.figure(figsize=(8, 4.5))
    plt.bar(teams, vals)
    plt.ylabel("Demo title probability")
    plt.title("Forecast VAR demo: top tournament favourites")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(FIG / "top_tournament_favourites.png", dpi=160)
    plt.close()


def save_preflight() -> None:
    p = preflight_forecast_context()
    labels = ["groups", "teams", "feature rows"]
    vals = [p["group_count"], p["team_count"], p["feature_rows"]]
    plt.figure(figsize=(7.5, 4.2))
    plt.bar(labels, vals)
    plt.ylabel("Count")
    plt.title("Forecast pre-flight: field and feature readiness")
    for i, v in enumerate(vals):
        plt.text(i, v + max(vals) * 0.02, str(v), ha="center")
    plt.ylim(0, max(vals) * 1.2)
    plt.tight_layout()
    plt.savefig(FIG / "preflight_readiness.png", dpi=160)
    plt.close()


def save_eval_summary() -> None:
    base_path = PROJECT_ROOT / "reports/summary_baseline_mock.json"
    ground_path = PROJECT_ROOT / "reports/summary_grounded_mock.json"
    if not base_path.exists() or not ground_path.exists():
        return
    base = json.loads(base_path.read_text(encoding="utf-8"))
    ground = json.loads(ground_path.read_text(encoding="utf-8"))
    metrics = ["pass_rate", "preflight_recall", "source_support_precision", "factual_citation_support", "model_citation_support", "probability_sanity_rate"]
    x = range(len(metrics))
    width = 0.35
    plt.figure(figsize=(10, 4.8))
    plt.bar([i - width / 2 for i in x], [base[m] for m in metrics], width, label="Baseline")
    plt.bar([i + width / 2 for i in x], [ground[m] for m in metrics], width, label="Grounded")
    plt.xticks(list(x), metrics, rotation=25, ha="right")
    plt.ylim(0, 1.1)
    plt.ylabel("Score")
    plt.title("Forecast agent evaluation: source-supported prediction discipline")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "eval_summary.png", dpi=160)
    plt.close()


def main() -> None:
    save_group_d()
    save_top_favourites()
    save_preflight()
    save_eval_summary()
    print(f"Wrote figures to {FIG}")


if __name__ == "__main__":
    main()

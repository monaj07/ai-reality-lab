from __future__ import annotations

import csv
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _probs_from_ratings(rating_a: float, rating_b: float) -> dict[str, float]:
    diff = rating_a - rating_b
    p_a_no_draw = 1.0 / (1.0 + 10 ** (-diff / 420.0))
    draw = 0.27 - min(0.09, abs(diff) / 1800.0)
    draw = max(0.18, min(0.30, draw))
    p_a = (1.0 - draw) * p_a_no_draw
    p_b = 1.0 - draw - p_a
    return {"A": p_a, "D": draw, "B": p_b}


def run_backtest(path: Path | None = None) -> dict:
    path = path or PROJECT_ROOT / "data/backtest/historical_match_sample.csv"
    rows = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            probs = _probs_from_ratings(float(row["rating_a"]), float(row["rating_b"]))
            actual = row["actual_result"]
            p = max(probs[actual], 1e-9)
            log_loss = -math.log(p)
            brier = sum((probs[k] - (1.0 if k == actual else 0.0)) ** 2 for k in ["A", "D", "B"])
            rows.append({**row, **{f"p_{k}": round(v, 4) for k, v in probs.items()}, "log_loss": log_loss, "brier": brier})
    n = len(rows)
    return {
        "matches": n,
        "mean_log_loss": round(sum(r["log_loss"] for r in rows) / n, 4),
        "mean_brier": round(sum(r["brier"] for r in rows) / n, 4),
        "rows": rows,
        "note": "Illustrative backtest harness. Replace sample ratings with timestamped historical ratings for a serious model audit.",
    }

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from sport_agent.designs import DESIGNS
from sport_agent.eval_harness import evaluate_all, evaluate_design, summarise, write_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate sport-agent designs.")
    parser.add_argument("--design", default="all", help="one design or all")
    parser.add_argument("--out-dir", default="reports")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.design == "all":
        summaries = evaluate_all(out_dir)
    else:
        if args.design not in DESIGNS:
            raise SystemExit(f"Unknown design: {args.design}")
        results = evaluate_design(args.design)
        summaries = [write_results(results, out_dir)]

    csv_path = out_dir / "summary_all_designs.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path

from forecast_var.eval_harness import evaluate
from forecast_var.config import DEFAULT_OPENAI_MODEL
from forecast_var.runner import run_agent

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["baseline_mock", "grounded_mock", "openai"], default="grounded_mock")
    parser.add_argument("--model", default=DEFAULT_OPENAI_MODEL)
    args = parser.parse_args()

    result = evaluate(lambda q: run_agent(q, mode=args.mode, model=args.model))
    (PROJECT_ROOT / "reports").mkdir(exist_ok=True)
    with open(PROJECT_ROOT / f"reports/eval_{args.mode}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    with open(PROJECT_ROOT / f"reports/summary_{args.mode}.json", "w", encoding="utf-8") as f:
        json.dump(result["summary"], f, ensure_ascii=False, indent=2)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

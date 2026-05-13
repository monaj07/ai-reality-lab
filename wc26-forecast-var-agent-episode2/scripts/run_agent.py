from __future__ import annotations

import argparse
import json
from forecast_var.runner import run_agent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--mode", choices=["baseline_mock", "grounded_mock", "openai"], default="grounded_mock")
    parser.add_argument("--model", default="gpt-4.1-mini")
    args = parser.parse_args()
    answer = run_agent(args.question, mode=args.mode, model=args.model)
    print(json.dumps(answer.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

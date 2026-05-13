#!/usr/bin/env python
from __future__ import annotations

import argparse
import json

from wc_reality.facts import FactStore
from wc_reality.mock_agents import answer_baseline, answer_grounded
from wc_reality.openai_agent import answer_with_openai


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the football grounded agent one question.")
    parser.add_argument("question")
    parser.add_argument("--agent", choices=["baseline", "grounded"], default="grounded")
    parser.add_argument("--backend", choices=["mock", "openai"], default="mock")
    parser.add_argument("--facts", default=None)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    store = FactStore.from_jsonl(args.facts)
    if args.agent == "baseline":
        result = answer_baseline(args.question, store)
    elif args.backend == "openai":
        result = answer_with_openai(args.question, store, model=args.model)
    else:
        result = answer_grounded(args.question, store)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

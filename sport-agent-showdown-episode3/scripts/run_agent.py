from __future__ import annotations

import argparse
import json

from sport_agent.designs import DESIGNS, run_design
from sport_agent.openai_agents import run_openai_triage_sync


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a sport-agent design.")
    parser.add_argument("question")
    parser.add_argument("--design", default="triage_handoff", help="single_agent, sequential_chain, triage_handoff, committee_referee, openai_triage")
    parser.add_argument("--model", default="gpt-4.1-mini")
    args = parser.parse_args()

    if args.design == "openai_triage":
        ans = run_openai_triage_sync(args.question, model=args.model)
        print(ans.model_dump_json(indent=2))
        return
    if args.design not in DESIGNS:
        raise SystemExit(f"Unknown design {args.design}. Choose from {DESIGNS} or openai_triage.")
    answer = run_design(args.question, args.design)
    print(answer.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

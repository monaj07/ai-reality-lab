from __future__ import annotations

import argparse
import json
from pathlib import Path

from forecast_var.tools import refresh_evidence_index, source_coverage_report

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the local Forecast VAR evidence index.")
    parser.add_argument("--include-live-api", action="store_true", help="Opt in to API-Football adapter if API_FOOTBALL_KEY is set.")
    args = parser.parse_args()

    refresh = refresh_evidence_index(include_live_api=args.include_live_api)
    coverage = source_coverage_report()
    (PROJECT_ROOT / "reports").mkdir(exist_ok=True)
    with open(PROJECT_ROOT / "reports/source_refresh.json", "w", encoding="utf-8") as f:
        json.dump({"refresh": refresh, "coverage": coverage}, f, ensure_ascii=False, indent=2)
    print(json.dumps(refresh, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

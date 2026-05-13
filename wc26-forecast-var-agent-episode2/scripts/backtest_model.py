from __future__ import annotations

import json
from pathlib import Path
from forecast_var.backtest import run_backtest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    result = run_backtest()
    (PROJECT_ROOT / "reports").mkdir(exist_ok=True)
    with open(PROJECT_ROOT / "reports/backtest_summary.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

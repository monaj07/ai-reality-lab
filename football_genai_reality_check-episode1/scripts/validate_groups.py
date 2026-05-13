#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from wc_reality.groups import load_groups, validate_groups


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the local 2026 World Cup group list.")
    parser.add_argument("--groups", default=None, help="Optional path to groups JSON.")
    parser.add_argument("--out", default="reports/group_validation.json")
    args = parser.parse_args()

    groups = load_groups(args.groups)
    report = validate_groups(groups)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"groups": groups, "validation": report}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

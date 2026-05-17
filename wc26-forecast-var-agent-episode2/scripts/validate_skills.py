#!/usr/bin/env python3
"""Validate local agent skill metadata.

This project uses small local agent skills under `.agents/skills`. They are not
packaged as standalone ChatGPT skills, but each `SKILL.md` still follows the
standard frontmatter convention:

---
name: skill-name
description: when and why the agent should use this skill.
---

The script intentionally avoids PyYAML so the validation works with the base
project dependencies.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    metadata: dict[str, str] = {}
    for line in text[4:end].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, text[end + len("\n---\n") :]


def validate_skill(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    errors: list[str] = []

    expected_name = path.parent.name
    name = metadata.get("name", "")
    description = metadata.get("description", "")

    if not metadata:
        errors.append("missing YAML frontmatter")
    if name != expected_name:
        errors.append(f"name must match folder name: expected {expected_name!r}, got {name!r}")
    if name and not NAME_RE.match(name):
        errors.append("name must be lowercase kebab-case")
    if not description:
        errors.append("description is required")
    elif len(description.split()) < 12:
        errors.append("description should include clear trigger/use context")
    if not body.strip():
        errors.append("body instructions are required")

    return {
        "skill": expected_name,
        "path": str(path.relative_to(ROOT)),
        "name": name,
        "description": description,
        "valid": not errors,
        "errors": errors,
    }


def main() -> int:
    reports = [validate_skill(path) for path in sorted(SKILLS_ROOT.glob("*/SKILL.md"))]
    ok = all(report["valid"] for report in reports)
    print(json.dumps({"valid": ok, "skills": reports}, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

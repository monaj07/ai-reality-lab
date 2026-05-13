from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


@lru_cache(maxsize=None)
def world_cup_groups() -> dict[str, Any]:
    return load_json(DATA / "facts" / "football_worldcup_2026_groups.json")


@lru_cache(maxsize=None)
def football_legacy_players() -> dict[str, Any]:
    return load_json(DATA / "facts" / "football_legacy_players.json")


@lru_cache(maxsize=None)
def f1_lineups() -> dict[str, Any]:
    return load_json(DATA / "facts" / "f1_2026_lineups.json")


@lru_cache(maxsize=None)
def f1_calendar() -> dict[str, Any]:
    return load_json(DATA / "facts" / "f1_2026_calendar_current.json")


@lru_cache(maxsize=None)
def f1_original_calendar_note() -> dict[str, Any]:
    return load_json(DATA / "facts" / "f1_2026_original_calendar_note.json")


@lru_cache(maxsize=None)
def chess_top_players() -> dict[str, Any]:
    return load_json(DATA / "facts" / "chess_fide_may_2026_top_players.json")


@lru_cache(maxsize=None)
def source_cards() -> list[dict[str, Any]]:
    return load_jsonl(DATA / "rag" / "source_cards.jsonl")


@lru_cache(maxsize=None)
def source_registry() -> dict[str, Any]:
    return load_json(DATA / "sources" / "source_registry.json")


def citation_detail(source_id: str) -> dict[str, str | None]:
    for card in source_cards():
        if card["source_id"] == source_id:
            return {
                "source_id": source_id,
                "title": card.get("title"),
                "url": card.get("url"),
                "retrieved_at": card.get("retrieved_at"),
            }
    for entry in source_registry().get("sources", []):
        if entry.get("source_id") == source_id:
            return {
                "source_id": source_id,
                "title": entry.get("title"),
                "url": entry.get("url"),
                "retrieved_at": None,
            }
    return {"source_id": source_id, "title": None, "url": None, "retrieved_at": None}

from __future__ import annotations

import csv
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _clean_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    return text


ALIASES = {
    "us": "USA",
    "usa": "USA",
    "united states": "USA",
    "america": "USA",
    "turkey": "Türkiye",
    "turkiye": "Türkiye",
    "cote d ivoire": "Côte d'Ivoire",
    "ivory coast": "Côte d'Ivoire",
    "curacao": "Curaçao",
    "south korea": "Korea Republic",
    "korea republic": "Korea Republic",
    "iran": "IR Iran",
    "ir iran": "IR Iran",
    "cape verde": "Cabo Verde",
    "cabo verde": "Cabo Verde",
    "dr congo": "Congo DR",
    "congo dr": "Congo DR",
    "bosnia": "Bosnia and Herzegovina",
    "bosnia herzegovina": "Bosnia and Herzegovina",
}


@lru_cache(maxsize=1)
def load_groups() -> dict[str, list[str]]:
    with open(PROJECT_ROOT / "data/facts/world_cup_2026_groups.json", encoding="utf-8") as f:
        return json.load(f)["groups"]


@lru_cache(maxsize=1)
def load_source_registry() -> list[dict[str, Any]]:
    with open(PROJECT_ROOT / "data/sources/source_registry.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_source_cards() -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    path = PROJECT_ROOT / "data/facts/source_cards.jsonl"
    with open(path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            cards[rec["id"]] = rec
    return cards


@lru_cache(maxsize=1)
def load_team_features() -> dict[str, dict[str, Any]]:
    path = PROJECT_ROOT / "data/sources/sample_team_features.csv"
    out: dict[str, dict[str, Any]] = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rec: dict[str, Any] = dict(row)
            for key in ["strength_rating", "fifa_rank_proxy", "recent_form_index", "travel_load_index", "host_advantage_points"]:
                rec[key] = float(rec[key])
            rec["fifa_rank_proxy"] = int(rec["fifa_rank_proxy"])
            rec["source_ids"] = [x for x in rec["source_ids"].split(";") if x]
            out[row["team"]] = rec
    return out


@lru_cache(maxsize=1)
def all_teams() -> list[str]:
    teams: list[str] = []
    for group_teams in load_groups().values():
        teams.extend(group_teams)
    return teams


def normalize_team(name: str) -> str:
    cleaned = _clean_name(name)
    if cleaned in ALIASES:
        return ALIASES[cleaned]
    for team in all_teams():
        if _clean_name(team) == cleaned:
            return team
    raise KeyError(f"Unknown or non-qualified team: {name}")


def team_group(team: str) -> str | None:
    team = normalize_team(team)
    for group, teams in load_groups().items():
        if team in teams:
            return group
    return None


def citation(source_id: str, detail: str = "") -> dict[str, str]:
    card = load_source_cards().get(source_id, {})
    return {
        "id": f"CITE-{source_id}",
        "source_id": source_id,
        "title": card.get("title", source_id),
        "url": card.get("url", ""),
        "detail": detail or card.get("claim", ""),
    }

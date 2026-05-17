from __future__ import annotations

import csv
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "for", "from",
    "how", "i", "in", "is", "it", "of", "on", "or", "source", "sources", "the",
    "this", "to", "use", "what", "which", "who", "with", "world", "cup", "2026",
}


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
            rec.setdefault("supports", [])
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


def tokenise(text: str) -> set[str]:
    cleaned = _clean_name(text)
    return {tok for tok in cleaned.split() if tok and tok not in STOPWORDS and len(tok) > 1}


def search_source_cards(query: str, k: int = 5) -> list[dict[str, Any]]:
    """Tiny transparent RAG retriever over local source cards.

    It intentionally uses token overlap instead of a vector database so the tutorial can
    explain and test the retrieval step without hidden infrastructure.
    """
    q_tokens = tokenise(query)
    scored: list[tuple[float, dict[str, Any]]] = []
    for card in load_source_cards().values():
        text = " ".join(str(card.get(x, "")) for x in ["id", "title", "claim", "url"])
        text += " " + " ".join(card.get("supports", []))
        c_tokens = tokenise(text)
        overlap = len(q_tokens & c_tokens)
        score = overlap / max(len(q_tokens), 1)
        if _clean_name(card["id"]) in _clean_name(query):
            score += 1.0
        if score > 0:
            item = dict(card)
            item["score"] = round(score, 4)
            item["citation"] = citation(card["id"])
            scored.append((score, item))
    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [item for _, item in scored[:k]]


def source_support_labels(source_ids: list[str]) -> set[str]:
    cards = load_source_cards()
    labels: set[str] = set()
    for sid in source_ids:
        labels.update(cards.get(sid, {}).get("supports", []))
    return labels


def load_market_odds() -> list[dict[str, Any]]:
    """Load bundled sample odds used only for de-vig baseline demos."""
    path = PROJECT_ROOT / "data/sources/sample_market_odds.csv"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rec: dict[str, Any] = dict(row)
            # Accept both the current avg_* schema and an older decimal_* schema
            # so notebooks remain compatible with previous generated artifacts.
            rec["avg_odds_team_a"] = float(rec.get("avg_odds_team_a") or rec.get("decimal_odds_a"))
            rec["avg_odds_draw"] = float(rec.get("avg_odds_draw") or rec.get("decimal_odds_draw"))
            rec["avg_odds_team_b"] = float(rec.get("avg_odds_team_b") or rec.get("decimal_odds_b"))
            rec["as_of_utc"] = rec.get("as_of_utc") or rec.get("timestamp_utc") or "unknown"
            rows.append(rec)
    return rows


def search_evidence_index(query: str, k: int = 8) -> list[dict[str, Any]]:
    """Search the generated evidence index with transparent token overlap.

    This complements `search_source_cards`: source cards explain the source
    policy, while the evidence index includes team profiles, market snapshots,
    and curated notes.
    """
    from .source_adapters import load_evidence_index

    q_tokens = tokenise(query)
    scored: list[tuple[float, dict[str, Any]]] = []
    for doc in load_evidence_index():
        text = " ".join(str(doc.get(x, "")) for x in ["id", "title", "text", "source_id", "doc_type"])
        text += " " + " ".join(doc.get("supports", []))
        tokens = tokenise(text)
        overlap = len(q_tokens & tokens)
        score = overlap / max(len(q_tokens), 1)
        if score > 0:
            item = dict(doc)
            item["score"] = round(score, 4)
            item["citation"] = citation(doc.get("source_id", "SRC-EVIDENCE-INDEX"))
            scored.append((score, item))
    scored.sort(key=lambda x: (-x[0], x[1].get("id", "")))
    return [item for _, item in scored[:k]]

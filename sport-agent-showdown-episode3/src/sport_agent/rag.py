from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .data import source_cards

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def score(query: str, card: dict[str, Any]) -> float:
    q = Counter(tokenize(query))
    text = " ".join([card.get("title", ""), card.get("sport", ""), card.get("text", "")])
    c = Counter(tokenize(text))
    if not q:
        return 0.0
    overlap = sum(min(q[t], c[t]) for t in q)
    title_boost = 1.0 if any(t in tokenize(card.get("title", "")) for t in q) else 0.0
    return float(overlap) + title_boost


def search_source_cards(query: str, sport: str | None = None, top_k: int = 5) -> list[dict[str, Any]]:
    cards = source_cards()
    if sport and sport != "unknown":
        cards = [c for c in cards if c.get("sport") == sport]
    ranked = sorted(((score(query, c), c) for c in cards), key=lambda x: x[0], reverse=True)
    return [c | {"score": s} for s, c in ranked[:top_k] if s > 0]

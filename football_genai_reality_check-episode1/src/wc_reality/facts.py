from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "is",
    "it", "of", "on", "or", "the", "to", "was", "were", "what", "when", "where", "who",
    "will", "with", "this", "that", "than", "into", "do", "does", "did", "tell", "me",
    "which", "terms", "scheduled", "take", "place",
}

@dataclass(frozen=True)
class Fact:
    fact_id: str
    title: str
    claim: str
    source_title: str
    source_url: str
    tags: list[str]
    aliases: list[str]

    @classmethod
    def from_dict(cls, row: dict) -> "Fact":
        return cls(
            fact_id=row["fact_id"],
            title=row["title"],
            claim=row["claim"],
            source_title=row["source_title"],
            source_url=row["source_url"],
            tags=list(row.get("tags", [])),
            aliases=list(row.get("aliases", [])),
        )

    def to_dict(self) -> dict:
        return {
            "fact_id": self.fact_id,
            "title": self.title,
            "claim": self.claim,
            "source_title": self.source_title,
            "source_url": self.source_url,
            "tags": self.tags,
            "aliases": self.aliases,
        }

    def search_text(self) -> str:
        return " ".join([self.fact_id, self.title, self.claim, *self.tags, *self.aliases])


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_facts_path() -> Path:
    return project_root() / "data" / "facts" / "world_cup_2026_facts.jsonl"


def default_eval_path() -> Path:
    return project_root() / "data" / "eval" / "world_cup_eval_set.jsonl"


def tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in WORD_RE.findall(text) if tok.lower() not in STOPWORDS]


def load_jsonl(path: str | Path) -> list[dict]:
    rows: list[dict] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

class FactStore:
    """Tiny lexical fact store for an auditable first episode.

    It is intentionally simple: the interface can later be backed by embeddings, hybrid search,
    OpenAI File Search, or a proper retrieval service without changing the agent/eval contract.
    """

    def __init__(self, facts: Iterable[Fact]):
        self.facts = list(facts)
        self.by_id = {fact.fact_id: fact for fact in self.facts}
        self._doc_tokens = {fact.fact_id: tokenize(fact.search_text()) for fact in self.facts}
        self._idf = self._compute_idf(self._doc_tokens.values())

    @classmethod
    def from_jsonl(cls, path: str | Path | None = None) -> "FactStore":
        return cls(Fact.from_dict(row) for row in load_jsonl(path or default_facts_path()))

    @staticmethod
    def _compute_idf(docs: Iterable[list[str]]) -> dict[str, float]:
        docs = list(docs)
        n_docs = max(len(docs), 1)
        df: dict[str, int] = {}
        for toks in docs:
            for tok in set(toks):
                df[tok] = df.get(tok, 0) + 1
        return {tok: math.log((1 + n_docs) / (1 + count)) + 1.0 for tok, count in df.items()}

    def get(self, fact_id: str) -> Fact | None:
        return self.by_id.get(fact_id)

    def search(self, query: str, k: int = 5) -> list[dict]:
        query_tokens = tokenize(query)
        scored: list[tuple[float, Fact]] = []
        for fact in self.facts:
            doc_tokens = self._doc_tokens[fact.fact_id]
            doc_counts = {tok: doc_tokens.count(tok) for tok in set(doc_tokens)}
            score = 0.0
            for tok in query_tokens:
                if tok in doc_counts:
                    score += (1.0 + math.log(doc_counts[tok])) * self._idf.get(tok, 1.0)
            alias_text = " ".join([fact.title, *fact.aliases]).lower()
            if any(tok in alias_text for tok in query_tokens):
                score += 0.5
            if score > 0:
                scored.append((score, fact))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [self._format_search_hit(fact, score) for score, fact in scored[:k]]

    @staticmethod
    def _format_search_hit(fact: Fact, score: float) -> dict:
        return {
            "fact_id": fact.fact_id,
            "title": fact.title,
            "claim": fact.claim,
            "source_title": fact.source_title,
            "source_url": fact.source_url,
            "score": round(score, 4),
        }

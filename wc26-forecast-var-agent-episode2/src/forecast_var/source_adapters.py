from __future__ import annotations

"""Small source-ingestion layer for Forecast VAR.

The goal is not to build a production data warehouse. It is to show a clean,
auditable pattern that can grow from bundled demo files to live football data:

source adapter -> evidence documents -> local JSONL index -> MCP retrieval tools.

The design is inspired by the source-index pattern in sport_mystic_ai, but this
module is original code and intentionally stays dependency-light for teaching.
"""

import csv
import json
import os
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INDEX_PATH = PROJECT_ROOT / "data/generated/evidence_index.jsonl"


@dataclass(frozen=True)
class EvidenceDocument:
    """A compact, source-aware retrieval document.

    The `supports` labels are intentionally explicit because the claim verifier
    uses them to decide whether a source can support a factual, model, market, or
    uncertainty claim.
    """

    id: str
    source_id: str
    title: str
    text: str
    sport: str = "football"
    doc_type: str = "source_card"
    url: str = ""
    as_of_utc: str = "2026-05-16T00:00:00Z"
    supports: tuple[str, ...] = ()
    metadata: dict[str, Any] | None = None

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["supports"] = list(self.supports)
        data["metadata"] = self.metadata or {}
        return data


class SourceAdapter:
    """Tiny adapter base class.

    Real adapters can fetch data. The bundled adapters below are offline and
    deterministic so tests/notebooks are reproducible.
    """

    name = "base"

    def documents(self) -> Iterable[EvidenceDocument]:
        raise NotImplementedError


class SourceCardAdapter(SourceAdapter):
    name = "source_cards"

    def documents(self) -> Iterable[EvidenceDocument]:
        path = PROJECT_ROOT / "data/facts/source_cards.jsonl"
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                yield EvidenceDocument(
                    id=f"CARD-{rec['id']}",
                    source_id=rec["id"],
                    title=rec.get("title", rec["id"]),
                    text=rec.get("claim", ""),
                    doc_type="source_card",
                    url=rec.get("url", ""),
                    supports=tuple(rec.get("supports", [])),
                    metadata={"card_id": rec["id"]},
                )


class TeamFeatureAdapter(SourceAdapter):
    name = "team_features"

    def documents(self) -> Iterable[EvidenceDocument]:
        path = PROJECT_ROOT / "data/sources/sample_team_features.csv"
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                team = row["team"]
                text = (
                    f"{team} belongs to Group {row['group']} and has demo strength "
                    f"rating {row['strength_rating']}, FIFA-rank proxy {row['fifa_rank_proxy']}, "
                    f"recent-form proxy {row['recent_form_index']}, travel-load proxy "
                    f"{row['travel_load_index']}, and host-advantage points "
                    f"{row['host_advantage_points']}. Notes: {row.get('notes', '')}"
                )
                yield EvidenceDocument(
                    id=f"TEAM-{team.replace(' ', '_')}",
                    source_id="SRC-SAMPLE-TEAM-PRIORS",
                    title=f"Demo team feature profile: {team}",
                    text=text,
                    doc_type="team_feature",
                    url="file://data/sources/sample_team_features.csv",
                    supports=("model_input", "team_strength_input", "demo_features", "source_coverage"),
                    metadata={"team": team, "group": row["group"], "source_ids": row.get("source_ids", "")},
                )


class MarketOddsAdapter(SourceAdapter):
    name = "sample_market_odds"

    def documents(self) -> Iterable[EvidenceDocument]:
        path = PROJECT_ROOT / "data/sources/sample_market_odds.csv"
        if not path.exists():
            return
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                text = (
                    f"Illustrative market odds for {row['team_a']} vs {row['team_b']}: "
                    f"{(row.get('avg_odds_team_a') or row.get('decimal_odds_a'))} / {(row.get('avg_odds_draw') or row.get('decimal_odds_draw'))} / "
                    f"{(row.get('avg_odds_team_b') or row.get('decimal_odds_b'))} as of {row['as_of_utc']}. "
                    f"These odds are demo inputs only and not betting advice."
                )
                yield EvidenceDocument(
                    id=f"MARKET-{row['match_id']}",
                    source_id="SRC-SAMPLE-MARKET-ODDS",
                    title=f"Demo market baseline: {row['team_a']} vs {row['team_b']}",
                    text=text,
                    doc_type="market_odds",
                    url="file://data/sources/sample_market_odds.csv",
                    as_of_utc=row.get("as_of_utc") or row.get("timestamp_utc") or "unknown",
                    supports=("market_baseline", "model_input", "source_coverage", "uncertainty"),
                    metadata=dict(row),
                )


class CuratedEvidenceAdapter(SourceAdapter):
    name = "curated_evidence"

    def documents(self) -> Iterable[EvidenceDocument]:
        path = PROJECT_ROOT / "data/sources/curated_evidence.jsonl"
        if not path.exists():
            return
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                yield EvidenceDocument(
                    id=rec["id"],
                    source_id=rec.get("source_id", "SRC-CURATED-EVIDENCE"),
                    title=rec.get("title", rec["id"]),
                    text=rec.get("text", ""),
                    sport=rec.get("sport", "football"),
                    doc_type="curated_note",
                    url=rec.get("url", "file://data/sources/curated_evidence.jsonl"),
                    as_of_utc=rec.get("as_of_utc", "2026-05-16T00:00:00Z"),
                    supports=tuple(rec.get("supports", [])),
                    metadata={k: v for k, v in rec.items() if k not in {"id", "title", "text", "supports"}},
                )


class APIFootballAdapter(SourceAdapter):
    """Optional live adapter stub for API-Football.

    It is deliberately not used by default. When enabled with an API key, it
    writes compact fixture evidence; production code should add caching,
    retries, rate-limit handling, and stricter schema validation.
    """

    name = "api_football_optional"

    def __init__(self, league_id: int = 1, season: int = 2026, timeout: int = 20) -> None:
        self.league_id = league_id
        self.season = season
        self.timeout = timeout

    def documents(self) -> Iterable[EvidenceDocument]:
        api_key = os.getenv("API_FOOTBALL_KEY")
        if not api_key:
            return []
        params = urllib.parse.urlencode({"league": self.league_id, "season": self.season})
        url = f"https://v3.football.api-sports.io/fixtures?{params}"
        req = urllib.request.Request(url, headers={"x-apisports-key": api_key})
        with urllib.request.urlopen(req, timeout=self.timeout) as response:  # nosec B310 - opt-in demo adapter
            payload = json.loads(response.read().decode("utf-8"))
        docs: list[EvidenceDocument] = []
        for item in payload.get("response", [])[:200]:
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            home = teams.get("home", {}).get("name", "unknown")
            away = teams.get("away", {}).get("name", "unknown")
            kickoff = fixture.get("date", "unknown")
            docs.append(
                EvidenceDocument(
                    id=f"API-FOOTBALL-FIXTURE-{fixture.get('id', len(docs))}",
                    source_id="SRC-API-FOOTBALL",
                    title=f"API-Football fixture: {home} vs {away}",
                    text=f"API-Football fixture {home} vs {away}, kickoff {kickoff}.",
                    doc_type="live_fixture",
                    url="https://www.api-football.com/",
                    as_of_utc="live_fetch",
                    supports=("live_adapter", "structured_match_data", "source_coverage"),
                    metadata={"fixture_id": fixture.get("id"), "home": home, "away": away, "kickoff": kickoff},
                )
            )
        return docs


def default_adapters(include_live_api: bool = False) -> list[SourceAdapter]:
    adapters: list[SourceAdapter] = [
        SourceCardAdapter(),
        TeamFeatureAdapter(),
        MarketOddsAdapter(),
        CuratedEvidenceAdapter(),
    ]
    if include_live_api:
        adapters.append(APIFootballAdapter())
    return adapters


def build_evidence_index(
    output_path: Path | None = None,
    *,
    include_live_api: bool = False,
) -> dict[str, Any]:
    """Build the local evidence index used by the RAG/MCP tools."""

    output_path = output_path or DEFAULT_INDEX_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    docs: list[dict[str, Any]] = []
    adapter_counts: dict[str, int] = {}
    for adapter in default_adapters(include_live_api=include_live_api):
        records = [doc.to_json() for doc in adapter.documents()]
        adapter_counts[adapter.name] = len(records)
        docs.extend(records)
    with open(output_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    return {
        "output_path": str(output_path.relative_to(PROJECT_ROOT)),
        "document_count": len(docs),
        "adapter_counts": adapter_counts,
        "include_live_api": include_live_api,
    }


def load_evidence_index(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or DEFAULT_INDEX_PATH
    if not path.exists():
        build_evidence_index(path)
    docs: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
    return docs

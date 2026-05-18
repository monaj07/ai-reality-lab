# Source adapters and evidence index

Forecast VAR uses a small source-ingestion layer that keeps the episode stand-alone, auditable, and simple.

## Design

```text
source adapters
  -> EvidenceDocument objects
  -> data/generated/evidence_index.jsonl
  -> MCP retrieval tools
  -> typed claims + claim verifier
```

The agent does **not** ask the LLM to invent forecasts from prose. It uses deterministic Python tools for probabilities, then asks the LLM path to explain them with citations and uncertainty.

## Bundled adapters

| Adapter | File | Purpose |
|---|---|---|
| `SourceCardAdapter` | `data/facts/source_cards.jsonl` | Source-policy and claim-support cards |
| `TeamFeatureAdapter` | `data/sources/sample_team_features.csv` | Demo team-strength profiles for all 48 teams |
| `MarketOddsAdapter` | `data/sources/sample_market_odds.csv` | De-vig market-baseline demonstration |
| `CuratedEvidenceAdapter` | `data/sources/curated_evidence.jsonl` | Human-reviewed policy/context notes |
| `APIFootballAdapter` | optional, env-gated | Example live API adapter skeleton |

## Refresh

```bash
PYTHONPATH=src python scripts/refresh_sources.py
```

Optional live API-Football refresh, only if you have permitted access:

```bash
export API_FOOTBALL_KEY="..."
PYTHONPATH=src python scripts/refresh_sources.py --include-live-api
```

## Why not live by default?

The episode must be reproducible, cheap to run, and safe from licensing/rate-limit surprises. Live adapters are documented and opt-in. The default project uses bundled demo data and explains its limitations.

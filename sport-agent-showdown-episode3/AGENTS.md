# AGENTS.md

This repository contains Episode 3 of the **AI Reality Lab / Data VAR** series.

## Goal

Build and evaluate a multi-sport agent that can answer football, Formula 1 and chess questions while showing its sources. The project compares four agentic designs:

1. `single_agent`
2. `sequential_chain`
3. `triage_handoff`
4. `committee_referee`

## Setup commands

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Validation and tests

```bash
PYTHONPATH=src python scripts/validate_data.py
PYTHONPATH=src python scripts/evaluate.py --design all
PYTHONPATH=src pytest -q
```

## Engineering rules

- Keep offline deterministic mode working without an OpenAI key.
- Use OpenAI Agents SDK only in optional live paths.
- Do not add LangChain or Anthropic dependencies.
- Keep MCP tools read-only.
- Do not scrape live sports websites inside the offline project.
- Treat snapshot dates as part of the factual answer.
- If source cards disagree, surface the disagreement instead of silently resolving it.
- Never state a future sporting result as fact.
- Prefer `AGENTS.md`; do not add duplicate `Agents.md` files.

## Data rules

- Use `data/facts/` for structured local snapshots.
- Use `data/rag/source_cards.jsonl` for lightweight RAG source cards.
- Use `data/eval/episode3_eval_cases.jsonl` for evaluation cases.
- Any new fact must include a `source_id`, `source_url`, and `retrieved_at` date.

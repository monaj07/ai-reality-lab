# AGENTS.md - Forecast VAR source-aware edition

This file gives coding agents and human contributors the project rules for Episode 2.

## Project mission

Forecast VAR is a World Cup 2026 prediction-agent lab. It demonstrates how an agent can forecast while remaining auditable:

```text
pre-flight validation
source adapters
evidence index
MCP tools
agent skills
typed claims
claim verification
evaluation harness
```

The story is prediction-agent reliability, not football pundit certainty.

## Core rules

1. Keep the code small, readable, and tutorial-friendly.
2. Prefer deterministic Python tools for probabilities; do not make the LLM invent numbers.
3. Keep live source adapters opt-in and disabled by default.
4. Cite every factual, model-derived, market, rolling-state, and uncertainty claim.
5. Never present demo priors or sample odds as live official data.
6. Never provide betting advice.
7. Run `pytest`, `evaluate.py`, `validate_data.py`, and `validate_skills.py` after structural changes.
8. Keep every `.agents/skills/*/SKILL.md` file frontmatter-labeled with exactly `name` and `description`.
9. Use only `AGENTS.md`; do not add a duplicate `Agents.md`.

## Important files

```text
src/forecast_var/source_adapters.py  # source -> evidence-index layer
src/forecast_var/tournament_sim.py   # Monte Carlo and rolling forecast helpers
src/forecast_var/tools.py            # MCP-facing tool implementations
src/forecast_var/mock_agent.py       # deterministic offline agent for tests and notebook
src/forecast_var/openai_agent.py     # live OpenAI Agents SDK path
src/forecast_var/eval_harness.py     # agent evaluation metrics
mcp_servers/worldcup_forecast/server.py
```


## Live model policy

The offline notebook and tests use deterministic mock agents. The live OpenAI path defaults to:

```text
gpt-5.4-nano
```

Keep this default centralized in `src/forecast_var/config.py`. Do not hard-code model names in scripts or examples.

## Source adapter policy

Adapters should return compact, auditable evidence documents. Every document should include:

```text
id
source_id
title
text
supports labels
metadata
as_of_utc where relevant
```

Do not add scraping code for restricted websites. API adapters must be env-gated and documented.

## MCP policy

MCP tools should be read-only unless they explicitly write a local generated artifact such as `data/generated/evidence_index.jsonl`.

All tools should return:

```text
structured dictionaries
warnings where needed
citations when claims can be made from the output
```

## Evaluation policy

The grounded mock should pass all eval cases. The baseline mock should fail for meaningful reasons.

Run:

```bash
PYTHONPATH=src python scripts/refresh_sources.py
PYTHONPATH=src python scripts/validate_data.py
PYTHONPATH=src python scripts/validate_skills.py
PYTHONPATH=src python scripts/evaluate.py --mode baseline_mock
PYTHONPATH=src python scripts/evaluate.py --mode grounded_mock
PYTHONPATH=src pytest -q
```

## Style

- Use comments to explain non-obvious design choices.
- Keep functions short where possible.
- Prefer plain Python over framework-heavy abstractions.
- Avoid hidden global state except cached loaders in `data.py`.
- Add examples to README whenever adding a new user-facing command.

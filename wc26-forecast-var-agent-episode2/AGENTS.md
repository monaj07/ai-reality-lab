# AGENTS.md - Forecast VAR Episode 2

## Project purpose
This repository is a self-contained Data VAR / AI Reality Lab episode. It tests whether an agentic AI system can produce 2026 FIFA World Cup forecasts using explicit sources, MCP tools, agent skills, and calibrated uncertainty rather than unsupported football punditry.

## Canonical file
Use **AGENTS.md** as the only root-level coding-agent instruction file. Do not add `Agents.md`; duplicate case-variant files can drift and conflict across filesystems.

## Setup commands
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Validation commands
```bash
PYTHONPATH=src python scripts/validate_data.py
PYTHONPATH=src python scripts/evaluate.py --mode grounded_mock
PYTHONPATH=src python scripts/backtest_model.py
PYTHONPATH=src pytest -q
```

## Architecture boundaries
- Keep MCP tools read-only.
- Do not scrape websites in tests.
- Offline tests and notebooks must not require `OPENAI_API_KEY`.
- Live OpenAI API usage belongs in `src/forecast_var/openai_agent.py` and is activated only with `--mode openai`.
- Do not use LangChain or Anthropic wrappers.
- Agent skills live in `.agents/skills/*/SKILL.md`.
- The evaluation harness is the source of truth for response quality.

## Forecasting rules
- Report probabilities, not guarantees.
- Label bundled priors as demo data.
- Never recommend bets or present the output as betting advice.
- Refuse deterministic predictions such as "guarantee Argentina will win".
- Refresh live rankings, injuries, squads, lineups, weather, and market sources before public release.

## Data rules
- The project field contains 48 teams in 12 groups.
- Italy is intentionally absent because it did not qualify.
- The bundled `sample_team_features.csv` is illustrative, not an official forecast feed.

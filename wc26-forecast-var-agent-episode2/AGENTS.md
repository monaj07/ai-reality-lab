# AGENTS.md - Forecast VAR Episode 2

These instructions apply to coding agents working in this repository.

## Mission

Maintain a compact, readable World Cup 2026 prediction-agent project that demonstrates modern agent engineering without over-engineering.

The project story is:

> A World Cup prediction agent must validate its forecast context, retrieve source cards, use MCP tools, cite claims, separate facts from model outputs, and refuse fake certainty.

Do not turn this repository into a generic factual-QA episode. Keep changes aligned with the Forecast VAR prediction narrative.

## Core principles

1. **Prediction discipline**
   - Never present future outcomes as certain.
   - Report probabilities and uncertainty.
   - Separate factual claims, model inputs, model outputs, scenario assumptions, and guardrails.

2. **Forecast pre-flight first**
   - Forecasting should be gated by `preflight_forecast_context()`.
   - The pre-flight check validates the 12 groups, 48 teams, unique field, matching feature rows, and source registry readiness.

3. **MCP as the tool boundary**
   - Add new agent-callable functionality through `mcp_servers/worldcup_forecast/server.py` and `src/forecast_var/tools.py`.
   - Keep MCP tools read-only unless a future episode explicitly requires state changes.

4. **RAG should stay transparent**
   - The source-card retriever is intentionally simple.
   - Do not add a vector database unless the episode specifically needs to teach retrieval infrastructure.

5. **Claim support matters**
   - Add citations to all answer claims.
   - Use `claim_type` accurately.
   - Keep support labels in `data/facts/source_cards.jsonl` synchronized with the verifier rules in `src/forecast_var/tools.py`.

6. **No betting advice**
   - Do not turn market-implied probabilities into betting recommendations.
   - Market feeds are disabled by default in this tutorial.

7. **Live API path is optional**
   - Offline deterministic mock mode must remain the default for tests and notebooks.
   - The OpenAI path must remain runnable when `OPENAI_API_KEY` is set.

## Important files

```text
src/forecast_var/tools.py                 # MCP tool implementations and verifier
src/forecast_var/mock_agent.py            # Deterministic offline agents
src/forecast_var/openai_agent.py          # Live OpenAI Agents SDK path
src/forecast_var/eval_harness.py          # Evaluation metrics
mcp_servers/worldcup_forecast/server.py   # MCP server exposed to agents
data/facts/source_cards.jsonl             # Lightweight RAG corpus
data/sources/source_registry.json         # Source governance
data/eval/episode2_eval_cases.jsonl       # Benchmark cases
```

## Development checklist

Before packaging changes, run:

```bash
PYTHONPATH=src python scripts/validate_data.py
PYTHONPATH=src python scripts/evaluate.py --mode baseline_mock
PYTHONPATH=src python scripts/evaluate.py --mode grounded_mock
PYTHONPATH=src python scripts/backtest_model.py
PYTHONPATH=src python scripts/generate_figures.py
PYTHONPATH=src pytest -q
```

Expected test result:

```text
10 passed
```

## Style

- Prefer small functions and readable code.
- Avoid framework sprawl.
- Use OpenAI SDK / OpenAI Agents SDK for the live path.
- Do not introduce LangChain, Anthropic-specific code, or unnecessary orchestration frameworks.
- Keep examples reproducible offline.

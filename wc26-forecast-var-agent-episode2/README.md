# Episode 2 - Forecast VAR, Source-Aware Edition

**Episode title:** *I Built an AI to Predict the 2026 World Cup - Then Forced It to Prove Its Sources*

Forecast VAR is a compact agent-engineering project for a football-themed GenAI episode. The agent predicts 2026 FIFA World Cup outcomes, but it is not allowed to behave like a vibes-based pundit. Before it produces probabilities, it must validate the tournament field, retrieve evidence, call deterministic forecast tools, attach claim-level citations, compare model output against available baselines, and pass a strict evaluation harness.

This source-aware edition adds the best reusable ideas from the `sport_mystic_ai` reference repository while keeping Forecast VAR's own architecture clean and explainable:

- source adapters,
- local evidence index,
- market-baseline comparison,
- whole-tournament Monte Carlo,
- rolling forecasts after completed results,
- source-coverage scoring,
- stronger evaluation cases.

The project runs fully offline with deterministic mock agents, and it also includes a live OpenAI Agents SDK path that can call the local MCP server when `OPENAI_API_KEY` is set.

---

## Storyline

> Can a prediction agent forecast the 2026 World Cup while showing its sources, model inputs, uncertainty, data gaps, and unsupported-claim checks?

The episode arc is:

```text
1. A naive prediction agent makes confident claims.
2. Forecast VAR runs pre-flight validation before forecasting.
3. It builds a source-aware evidence index.
4. It compares its model with a de-vig sample market baseline.
5. It runs a Monte Carlo tournament simulation.
6. It demonstrates rolling forecasts after a completed-result state.
7. It evaluates every answer for tools, skills, citations, source support, probability sanity, and abstention.
```

---

## Project layout

```text
wc26-forecast-var-agent-episode2-source-aware/
├── AGENTS.md
├── README.md
├── docs/
│   ├── source_adapters.md
│   ├── prediction_upgrade_notes.md
│   └── monte_carlo_vs_llm.md
├── data/
│   ├── facts/
│   │   ├── world_cup_2026_groups.json
│   │   └── source_cards.jsonl
│   ├── sources/
│   │   ├── sample_team_features.csv
│   │   ├── sample_market_odds.csv
│   │   ├── curated_evidence.jsonl
│   │   ├── adapter_config.example.json
│   │   └── source_registry.json
│   ├── generated/
│   │   └── evidence_index.jsonl
│   ├── examples/
│   │   └── rolling_results_group_d.json
│   ├── eval/
│   │   └── episode2_eval_cases.jsonl
│   └── backtest/
│       └── historical_match_sample.csv
├── .agents/skills/
│   ├── forecast-preflight/
│   ├── citation-discipline/
│   ├── source-triage/
│   ├── forecast-modeling/
│   ├── scenario-analysis/
│   ├── uncertainty-calibration/
│   ├── source-adapter-governance/
│   ├── monte-carlo-forecasting/
│   └── eval-review/
├── mcp_servers/worldcup_forecast/server.py
├── src/forecast_var/
│   ├── data.py
│   ├── source_adapters.py
│   ├── tournament_sim.py
│   ├── tools.py
│   ├── forecast_model.py
│   ├── mock_agent.py
│   ├── openai_agent.py
│   ├── eval_harness.py
│   ├── backtest.py
│   ├── skills.py
│   └── schemas.py
├── scripts/
│   ├── refresh_sources.py
│   ├── run_agent.py
│   ├── evaluate.py
│   ├── validate_data.py
│   ├── backtest_model.py
│   └── generate_figures.py
├── notebooks/
│   ├── 02_forecast_var_prediction_agent.ipynb
│   └── 02_forecast_var_prediction_agent.executed.ipynb
├── figures/
└── reports/
```

---

## Quick start

```bash
cd wc26-forecast-var-agent-episode2-source-aware

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Refresh the local evidence index:

```bash
PYTHONPATH=src python scripts/refresh_sources.py
```

Validate the data and local agent-skill metadata:

```bash
PYTHONPATH=src python scripts/validate_data.py
PYTHONPATH=src python scripts/validate_skills.py
```

Run all tests:

```bash
PYTHONPATH=src pytest -q
```

Expected result:

```text
16 passed
```

---

## Main agent examples

### 1. Pre-flight validation

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Before forecasting the 2026 World Cup, run the pre-flight validation and tell me whether the context is ready." \
  --mode grounded_mock
```

What this demonstrates:

- 12 groups,
- 48 teams,
- 48 feature rows,
- generated evidence index,
- source-registry readiness,
- no forecast until validation passes.

### 2. Group forecast

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Who is the favourite to win Group D and how certain is that?" \
  --mode grounded_mock
```

What this demonstrates:

- group-level Monte Carlo,
- probability answer,
- uncertainty warning,
- field/source/model citations.

### 3. Source coverage report

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Give me a source coverage report before using the forecast agent for public predictions." \
  --mode grounded_mock
```

What this demonstrates:

- official field data coverage,
- demo-team-prior coverage,
- market-baseline coverage,
- missing live injury/lineup coverage,
- adapter slots that require permitted access.

### 4. Model vs market baseline

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Compare the model against the sample market baseline for USA vs Australia." \
  --mode grounded_mock
```

What this demonstrates:

- 1X2 model probabilities,
- de-vig sample market probabilities,
- bookmaker-margin disclosure,
- no betting advice,
- data gaps.

### 5. Whole-tournament Monte Carlo

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Run a Monte Carlo tournament simulation and show the top champion probabilities." \
  --mode grounded_mock
```

What this demonstrates:

- approximate group + knockout simulation,
- champion probabilities,
- bracket approximation warning,
- simulation-output claim type.

### 6. Rolling forecast after a completed-result state

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "After USA beat Australia 2-1, run a rolling Group D forecast." \
  --mode grounded_mock
```

What this demonstrates:

- completed results are locked,
- remaining fixtures are simulated,
- rolling-state claims are cited,
- the agent explains what is still uncertain.

### 7. OpenAI API live path

```bash
export OPENAI_API_KEY="your_key_here"

PYTHONPATH=src python scripts/run_agent.py \
  "Compare the model against the sample market baseline for USA vs Australia." \
  --mode openai \
  --model gpt-5.4-nano
```

The OpenAI path uses the Agents SDK, a local stdio MCP server, required tool use, static tool filtering, and strict `AgentAnswer` structured output. The same local claim verifier audits the final structured answer.


---

## Monte Carlo vs the OpenAI model

This project deliberately separates the **agent model** from the **forecasting model**.

```text
gpt-5.4-nano
= live agent brain, router, tool caller, explainer, and source-disciplined narrator

Python Monte Carlo simulator
= deterministic tournament forecasting engine exposed through MCP
```

In live mode, `gpt-5.4-nano` reads the user question, selects relevant skills, retrieves source cards, runs the pre-flight gate, calls MCP forecast tools, and explains the result. It should **not** invent probabilities from intuition. The probability numbers come from deterministic Python tools such as `forecast_match_with_context`, `forecast_group`, and `simulate_tournament`.

A Monte Carlo simulation means: run the tournament many times using probabilistic match outcomes, then count how often each team reaches each stage. Instead of saying “Brazil are stronger, so Brazil definitely win,” the simulator repeatedly samples realistic-but-random tournament paths. After thousands of runs, we get a distribution such as champion probability, finalist probability, and semifinal probability.

```text
User question
   ↓
gpt-5.4-nano Forecast VAR agent
   ↓
MCP tool call: simulate_tournament
   ↓
Python Monte Carlo engine
   ↓
champion / finalist / semifinal probabilities
   ↓
gpt-5.4-nano explanation + caveats + citations
   ↓
claim verifier + evaluation harness
```

Think of it like a broadcast team:

```text
gpt-5.4-nano = the presenter / analyst who asks the right questions and explains the drama
Monte Carlo simulator = the stats department that produces the numbers
MCP = the controlled phone line between them
Evaluation harness = the fact-checking desk
```

This design is important for agent engineering. If the language model freehands probabilities, the answer may sound confident but cannot be audited. If the model calls a deterministic simulator, we can reproduce the result, inspect the assumptions, compare it to source coverage, and evaluate whether the final answer overstated the forecast.

For a standalone version of this explanation, see `docs/monte_carlo_vs_llm.md`.

The default live model is `gpt-5.4-nano`. OpenAI's model documentation describes it as a GPT-5.4-class model designed for high-volume tasks where speed and cost matter, including classification, data extraction, ranking, and sub-agents. The same page lists support for structured outputs, function calling, skills, and MCP, which makes it a good default for this experimental agent-orchestration path.

---

## Source-aware architecture

```text
source adapters
  ↓
EvidenceDocument objects
  ↓
data/generated/evidence_index.jsonl
  ↓
MCP tools: search_evidence_index, source_coverage_report, forecast_match_with_context
  ↓
Agent skills: source-adapter-governance, forecast-modeling, uncertainty-calibration
  ↓
Typed claims + citations
  ↓
claim verifier + eval harness
```

### Why use adapters?

A prediction agent gets better when it can ingest new evidence without rewriting the agent. Adapters make each source explicit:

```text
SourceCardAdapter       -> source policy and support labels
TeamFeatureAdapter      -> bundled feature table for all 48 teams
MarketOddsAdapter       -> sample de-vig market comparison
CuratedEvidenceAdapter  -> human-reviewed notes and policies
APIFootballAdapter      -> optional live API-Football skeleton
```

### Why keep live sources off by default?

The episode must be reproducible and safe to run without API keys, rate-limit issues, or licensing surprises. The live API-Football adapter is present as a documented, opt-in example. It is not used in tests or notebook execution.

---

## MCP tools

The MCP server lives at:

```text
mcp_servers/worldcup_forecast/server.py
```

It exposes these read-only or local-only tools:

```text
search_source_cards
search_evidence_index
refresh_evidence_index
preflight_forecast_context
validate_tournament_field
get_source_registry
source_coverage_report
list_groups
get_team_inputs
forecast_match
forecast_match_with_context
extract_market_baseline
forecast_group
rank_teams
simulate_tournament
rolling_group_forecast
explain_model
verify_claims_against_sources
```

`refresh_evidence_index` writes only a local JSONL file under `data/generated/`.

---

## Agent skills

Skills are stored in `.agents/skills/<skill-name>/SKILL.md`. Each skill file starts with YAML frontmatter containing exactly `name` and `description`, followed by concise procedural instructions. The metadata is intentionally included even though these are internal project skill cards, because it keeps the skill layer discoverable, validates cleanly, and mirrors the shape of formal ChatGPT Skills.

Example:

```markdown
---
name: monte-carlo-forecasting
description: run and explain tournament simulations through deterministic tools. use when a question asks for monte carlo simulations, champion probabilities, rolling forecasts, bracket paths, or post-result updates.
---

# monte-carlo-forecasting

Use this skill when a question asks for tournament simulation, champion probabilities, rolling forecasts, or changes after completed results.
```

Implemented skills:

```text
forecast-preflight
citation-discipline
source-triage
forecast-modeling
scenario-analysis
uncertainty-calibration
source-adapter-governance
monte-carlo-forecasting
eval-review
```

Validate the skill metadata with:

```bash
PYTHONPATH=src python scripts/validate_skills.py
```

Skills are procedural instructions, not data sources. For example:

- `source-adapter-governance` tells the agent to distinguish bundled data from live/refreshed sources.
- `monte-carlo-forecasting` tells the agent to disclose simulation limitations and locked results.
- `citation-discipline` tells the agent to cite every factual, model-derived, market, rolling, and uncertainty claim.

---

## RAG / evidence index

The project uses lightweight local RAG rather than a vector database.

```bash
PYTHONPATH=src python scripts/refresh_sources.py
```

This writes:

```text
data/generated/evidence_index.jsonl
```

Each evidence document has:

```json
{
  "id": "MARKET-G-D-USA-AUS",
  "source_id": "SRC-SAMPLE-MARKET-ODDS",
  "title": "Demo market baseline: USA vs Australia",
  "text": "Illustrative market odds for USA vs Australia...",
  "supports": ["market_baseline", "model_input", "source_coverage", "uncertainty"],
  "metadata": {...}
}
```

The claim verifier uses `supports` labels to check whether a cited source can support a claim.

---

## Evaluation harness

Run deterministic evals:

```bash
PYTHONPATH=src python scripts/evaluate.py --mode baseline_mock
PYTHONPATH=src python scripts/evaluate.py --mode grounded_mock
```

The harness checks:

```text
pass_rate
tool_recall
skill_recall
preflight_recall
citation_recall
source_support_precision
factual_citation_support
model_citation_support
unsupported_factual_claim_rate
unsupported_prediction_claim_rate
abstention_accuracy
probability_sanity_rate
```

Current deterministic results:

| Agent | Cases | Pass rate | Tool recall | Skill recall | Pre-flight recall | Citation recall | Source support precision | Unsupported claim rate | Abstention accuracy | Probability sanity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline mock | 14 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0.714 | 0.429 |
| Grounded mock | 14 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 |

---

## Backtest-style check

```bash
PYTHONPATH=src python scripts/backtest_model.py
```

Current illustrative output:

```json
{
  "matches": 12,
  "mean_log_loss": 1.1194,
  "mean_brier": 0.669,
  "note": "Illustrative backtest harness. Replace sample ratings with timestamped historical ratings for a serious model audit."
}
```

This backtest is intentionally small. It proves the scoring pattern, not model superiority.

---

## Figures and notebook

Generate figures:

```bash
PYTHONPATH=src python scripts/generate_figures.py
```

The notebook tells the end-to-end story:

```text
notebooks/02_forecast_var_prediction_agent.executed.ipynb
```

Included figures:

```text
figures/preflight_readiness.png
figures/source_coverage_status.png
figures/model_vs_market_usa_australia.png
figures/monte_carlo_champion_probabilities.png
figures/group_d_winner_probabilities.png
figures/top_tournament_favourites.png
figures/eval_summary.png
```

---

## What was borrowed from `sport_mystic_ai`?

Only architectural ideas:

```text
source adapters
evidence index
rolling forecast mode
Brier/log-loss scoring
market-baseline roadmap
whole-tournament forecast structure
```

No source code was copied. The Forecast VAR implementation remains OpenAI Agents SDK + MCP + skills + local evaluation harness.

---

## Safety and accuracy limits

Forecast VAR is an educational agent-engineering project.

It does **not** provide:

```text
betting advice
certain future outcomes
official FIFA predictions
licensed live odds
licensed live injury/lineup feeds
production-grade market modelling
```

Before public or serious forecasting, replace demo priors with timestamped, licensed, and validated sources; rerun source coverage; rerun evaluation; and check calibration.

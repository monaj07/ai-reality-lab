# Episode 2 - Forecast VAR, Source-Aware Edition

**Episode title:** *I Built an AI to Predict the 2026 World Cup - Then Forced It to Prove Its Sources*

Forecast VAR is a compact agent-engineering project for a football-themed GenAI episode. The agent predicts 2026 FIFA World Cup outcomes, but it is not allowed to behave like a vibes-based pundit. Before it produces probabilities, it must validate the tournament field, retrieve evidence, call deterministic forecast tools, attach claim-level citations, compare model output against available baselines, and pass a strict evaluation harness.

The name is a football pun. In football, VAR means Video Assistant Referee. In this project, Forecast VAR is the review booth for AI forecasts: it validates inputs, audits evidence, checks claims, and refuses unsupported certainty before a prediction is presented.

This source-aware edition is designed as a stand-alone `ai-reality-lab` episode with a clean, explainable architecture:

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
wc26-forecast-var-agent-episode2/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── docs/
│   ├── monte_carlo_vs_llm.md
│   ├── prediction_upgrade_notes.md
│   ├── python_mcp_intro.md
│   └── source_adapters.md
├── data/
│   ├── backtest/
│   │   └── historical_match_sample.csv
│   ├── eval/
│   │   └── episode2_eval_cases.jsonl
│   ├── examples/
│   │   └── rolling_results_group_d.json
│   ├── facts/
│   │   ├── source_cards.jsonl
│   │   └── world_cup_2026_groups.json
│   ├── generated/
│   │   └── evidence_index.jsonl
│   └── sources/
│       ├── adapter_config.example.json
│       ├── curated_evidence.jsonl
│       ├── sample_market_odds.csv
│       ├── sample_team_features.csv
│       └── source_registry.json
├── .agents/skills/
│   ├── eval-review/
│   ├── forecast-modeling/
│   ├── scenario-analysis/
│   ├── source-triage/
│   └── uncertainty-calibration/
├── mcp_servers/
│   └── worldcup_forecast/
│       └── server.py
├── src/forecast_var/
│   ├── __init__.py
│   ├── backtest.py
│   ├── config.py
│   ├── data.py
│   ├── eval_harness.py
│   ├── forecast_model.py
│   ├── mock_agent.py
│   ├── openai_agent.py
│   ├── runner.py
│   ├── schemas.py
│   ├── scorelines.py
│   ├── skills.py
│   ├── source_adapters.py
│   ├── tools.py
│   └── tournament_sim.py
├── scripts/
│   ├── backtest_model.py
│   ├── evaluate.py
│   ├── generate_figures.py
│   ├── refresh_sources.py
│   ├── run_agent.py
│   ├── validate_data.py
│   └── validate_skills.py
├── notebooks/
│   ├── 02_forecast_var_prediction_agent.executed.ipynb
│   └── 02_forecast_var_prediction_agent.ipynb
├── figures/
├── reports/
└── tests/
```

---

## Quick start

```bash
cd wc26-forecast-var-agent-episode2

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
21 passed
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

### 5. Match probabilities plus scoreline scenario

```bash
PYTHONPATH=src python - <<'PY'
from forecast_var.tools import forecast_match

forecast = forecast_match("France", "Iraq")
print(forecast["probabilities"])
print(forecast["scoreline_projection"]["scenario_scoreline"])
print(forecast["scoreline_projection"]["top_scorelines"])
PY
```

What this demonstrates:

- 1X2 probabilities still come from the deterministic model,
- exact-score candidates are calibrated to those probabilities,
- the displayed scenario scoreline is seeded and reproducible,
- the scenario scoreline is not a certainty or betting signal.

### 6. Whole-tournament Monte Carlo

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

### 7. Rolling forecast after a completed-result state

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

### 8. OpenAI API live path

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

In live mode, `gpt-5.4-nano` reads the user question, selects relevant skills, retrieves source cards, runs the pre-flight gate, calls MCP forecast tools, and explains the result. It should **not** invent probabilities from intuition. The probability numbers come from Python tools such as `forecast_match_with_context`, `forecast_group`, and `simulate_tournament`.

The clean split is:

```text
The LLM chooses the workflow and tool calls.
The tools perform the concrete data access and forecasting computation.
The LLM narrates the result with citations, caveats, and uncertainty labels.
```

For the live path, that means:

```text
1. User asks a forecasting question.
2. LLM decides which source, pre-flight, evidence, or forecast tools are relevant.
3. MCP tools execute deterministic Python code.
4. Python loads bundled data, source registry entries, evidence documents, team priors, or sample market rows.
5. Python forecasting tools compute probabilities or seeded simulation outputs.
6. LLM receives structured tool results.
7. LLM writes the answer, but should not invent or alter the probability numbers.
```

The LLM does not directly fetch from project sources in this codebase. It calls tools such as `search_source_cards`, `source_coverage_report`, `forecast_match_with_context`, `forecast_group`, and `simulate_tournament`; those tools decide exactly how to read local files or opt-in adapters. The forecast probabilities are therefore produced without LLM math.

A Monte Carlo simulation means: run the tournament many times using probabilistic match outcomes, then count how often each team reaches each stage. Instead of saying “Brazil are stronger, so Brazil definitely win,” the simulator repeatedly samples realistic-but-random tournament paths. After thousands of runs, we get a distribution such as champion probability, finalist probability, and semifinal probability.

Forecast VAR also has a small scoreline realism layer. The match model first computes 1X2 probabilities, then `scorelines.py` maps those probabilities and team ratings onto an exact-score grid from 0-0 through 9-9. The grid is calibrated so the total mass for home/team-a win, draw, and away/team-b win still matches the deterministic 1X2 model. A seeded scenario scoreline is then sampled from that grid. This means examples can include draws, 0-0s, 4-3s, 5-0s, and rare high-scoring tails while keeping the probability engine auditable.

Important caveat: the scoreline scenario is not "the predicted exact result." It is one reproducible scenario draw from a calibrated distribution. For serious forecasting, inspect the full 1X2 probabilities, top scoreline candidates, expected goals, source coverage, and data gaps together.

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

This design is important for agent engineering. If the language model freehands probabilities, the answer may sound confident but cannot be audited. If the model calls a tool, the numeric forecast can be reproduced when the code, bundled inputs, parameters, and simulator seed are the same. The live LLM API response is still not promised to be bit-for-bit deterministic, even with low temperature or seed controls. What becomes reproducible is the forecasting procedure and tool output; what becomes auditable is the LLM's tool trace, citations, structured claims, and final explanation.

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
Agent skills: source-triage, forecast-modeling, uncertainty-calibration
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

### Source governance

Source governance is the part of Forecast VAR that answers: "What sources exist, what can they support, are they bundled or live, and what are the licensing or safety limits?"

Two local files carry different parts of that contract:

```text
data/sources/source_registry.json
= source inventory and governance metadata
= source id, category, status, available fields, license notes

data/facts/source_cards.jsonl
= compact citation and support cards
= source id, title, URL, claim summary, supports labels
```

`source_registry.json` is the catalog. It tells the agent whether a source is bundled, refreshable, a placeholder, disabled by default, manual, paid, or subject to licensing checks. `source_cards.jsonl` is the citation layer. It tells the claim verifier what a cited source can support, such as `tournament_field`, `model_input`, `market_baseline`, `source_policy`, or `uncertainty`.

The folder split follows the same idea:

```text
data/sources/
= source-side inputs, sample priors, sample odds, curated source material, adapter config, and source registry

data/facts/
= curated forecast-facing facts and citation cards used directly for validation and grounding
```

So `data/sources/` is closer to "where the data comes from and how it may be used"; `data/facts/` is closer to "what compact facts or source cards the agent can cite."

### What does de-vig mean here?

Market odds include bookmaker margin, often called vig or overround. To de-vig the sample 1X2 odds, Forecast VAR converts each decimal odd into a raw implied probability with `1 / odds`, then normalizes the three outcomes so win/draw/win probabilities sum to 1. That gives a market-implied comparison baseline without treating the odds as betting advice.

Forecast VAR uses de-vig probabilities only to ask, "Is the demo model far away from this sample external baseline?" It does not use them to recommend wagers, claim live market consensus, or present the sample rows as licensed odds.

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
name: forecast-modeling
description: use the forecasting tools instead of free-form guessing when the user asks for match, group, ranking, market, or tournament probabilities.
---

# Skill: forecast-modeling

Use this skill when a question asks who is favourite, who will win, match probabilities, group probabilities, or tournament rankings.
```

Current on-disk skill cards:

```text
eval-review
forecast-modeling
scenario-analysis
source-triage
uncertainty-calibration
```

The router also uses a few built-in workflow labels for pre-flight, citation discipline, source-adapter governance, and Monte Carlo forecasting. Those are handled in `src/forecast_var/skills.py` instead of being separate skill folders.

Validate the skill metadata with:

```bash
PYTHONPATH=src python scripts/validate_skills.py
```

Skills are procedural instructions, not data sources. For example:

- `source-triage` tells the agent to distinguish bundled data from live/refreshed sources.
- `forecast-modeling` tells the agent to use tools for probabilities instead of free-form guessing.
- `uncertainty-calibration` tells the agent to avoid certainty claims and betting language.

---

## Mock agents

`src/forecast_var/mock_agent.py` contains deterministic offline agents used for demos, notebooks, and evals.

```text
run_baseline_mock
= intentionally weak agent
= no tools, no skills, no citations, overconfident unsupported answers

run_grounded_mock
= scripted source-aware agent
= selects workflow labels, retrieves source cards, runs pre-flight, calls forecast tools, creates typed claims, attaches citations, verifies claim support
```

The baseline mock exists so the evaluation harness has a bad comparator. It makes plausible-sounding but unsafe claims such as certainty about future results or uncited source claims. The grounded mock exists to show the desired behavior without requiring a live model call. It is keyword-driven and tailored to the project eval cases, so it is not meant to be a general chatbot; it is a reproducible teaching harness for the source-aware workflow.

In the live path, the OpenAI agent replaces the keyword routing with model reasoning, but the same design rule remains: the LLM routes and explains; deterministic tools produce the probability numbers and source-aware evidence outputs.

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

### Factual and model grounding

Forecast VAR grounds answers at the claim level. An answer is split into typed `ForecastClaim` records, each with citation ids. `verify_claims_against_sources` then checks whether those citation ids map to real source cards and whether the cards have `supports` labels appropriate for the claim type.

Factual grounding covers claims such as:

```text
field_fact
guardrail
source_policy
model_input
source_coverage
market_baseline
rolling_state
```

These claims should cite source cards that support the underlying fact, policy, input, coverage statement, market baseline, or completed-result state.

Model grounding covers claims such as:

```text
model_output
scenario_assumption
simulation_output
uncertainty
```

These claims should cite the model card, sample priors, simulation source, scenario assumptions, or uncertainty-supporting evidence. A model-derived claim is grounded when the answer makes clear that the number came from Forecast VAR's Python model or simulator, not from the LLM's intuition.

The verifier is deliberately lightweight. It does not fully parse natural language and prove every sentence semantically true. Instead, it enforces citation discipline: real citation ids must be attached, and cited source cards must carry support labels that match the claim type.

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

Before public or serious forecasting, replace demo priors with timestamped, licensed, and validated sources; rerun source coverage; rerun evaluation; and check calibration. Treat exact scores as scenario samples, not final claims.

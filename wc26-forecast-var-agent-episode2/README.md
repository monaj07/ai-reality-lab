# Episode 2 - Forecast VAR: A World Cup 2026 Prediction Agent That Shows Its Work

This is the replacement Episode 2 for the **Data VAR / AI Reality Lab** series.

Instead of another schedule/group-checking episode, this project builds a more compelling football topic:

> Can an agentic AI system forecast the 2026 FIFA World Cup using multiple source types, while showing uncertainty, citations, assumptions, and evaluation results?

The goal is not to create a gambling bot or a magic oracle. The goal is to build a transparent, auditable prediction agent that says:

```text
Here are the sources I used.
Here are the probabilities.
Here is what would change under a scenario.
Here is what I cannot know.
Here is how the forecast and the agent response were evaluated.
```

---

## Episode hook

Suggested title:

> **I Built an AI World Cup Prediction Agent. Then I Tested Whether It Was Just Making Things Up.**

Suggested opening:

> Everyone wants an AI to predict the 2026 World Cup. But a useful forecast agent should not just shout "Argentina" or "France". It should know the field, use sources, quantify uncertainty, explain assumptions, and refuse fake certainty.

---

## AGENTS.md vs Agents.md

Use only:

```text
AGENTS.md
```

You do **not** need `Agents.md` as well. This repo deliberately uses only `AGENTS.md` to avoid case-sensitive/case-insensitive filesystem conflicts and duplicate instructions drifting over time.

---

## What is implemented

```text
wc26-forecast-var-episode2/
├── AGENTS.md
├── README.md
├── requirements.txt
├── data/
│   ├── facts/
│   │   ├── world_cup_2026_groups.json
│   │   └── source_cards.jsonl
│   ├── sources/
│   │   ├── source_registry.json
│   │   └── sample_team_features.csv
│   ├── eval/
│   │   └── episode2_eval_cases.jsonl
│   └── backtest/
│       └── historical_match_sample.csv
├── .agents/skills/
│   ├── source-triage/SKILL.md
│   ├── forecast-modeling/SKILL.md
│   ├── uncertainty-calibration/SKILL.md
│   ├── scenario-analysis/SKILL.md
│   └── eval-review/SKILL.md
├── mcp_servers/worldcup_forecast/server.py
├── src/forecast_var/
│   ├── data.py
│   ├── tools.py
│   ├── forecast_model.py
│   ├── mock_agent.py
│   ├── openai_agent.py
│   ├── eval_harness.py
│   ├── backtest.py
│   └── schemas.py
├── scripts/
├── tests/
├── figures/
├── reports/
└── notebooks/
```

---

## Source strategy: "all possible sources" as a registry

A serious World Cup prediction agent should not pretend one CSV is enough. This project implements a **source registry** with bundled, refreshable, placeholder, manual/paid, and disabled sources.

The registry is stored in:

```text
data/sources/source_registry.json
```

It includes source categories such as:

| Source type | Example | Status in this repo | Purpose |
|---|---|---|---|
| Official tournament field | FIFA World Cup 2026 page | Bundled + refreshable | Qualified teams, groups, schedule |
| Cross-check source | Wikipedia 2026 World Cup page | Bundled cross-check | Format, teams, groups |
| Official ranking | FIFA/Coca-Cola World Rankings | Adapter placeholder | Team-strength input |
| Elo-style ratings | World Football Elo / similar | Adapter placeholder | Team-strength input |
| Club strength proxy | ClubElo API | Adapter placeholder | Player-pool strength proxy |
| Historical results/odds | football-data style CSVs | Adapter placeholder | Backtesting and priors |
| Injury/suspension news | Licensed/manual feed | Manual or paid adapter | Availability adjustments |
| Betting market consensus | Licensed odds provider | Disabled by default | External probabilistic signal, not betting advice |
| Bundled priors | sample_team_features.csv | Demo only | Reproducible offline notebook/tests |

The point: the agent can be extended to real sources, but the repo stays legal, reproducible, and cheap by default.

---

## Current field

The project stores the full 48-team field in:

```text
data/facts/world_cup_2026_groups.json
```

Italy is not included because Italy did not qualify. The validator explicitly checks this:

```bash
PYTHONPATH=src python scripts/validate_data.py
```

Expected highlights:

```json
{
  "group_count": 12,
  "team_count": 48,
  "unique_team_count": 48,
  "italy_in_field": false,
  "valid": true
}
```

---

## Forecasting model

The bundled model is intentionally compact and readable:

```text
team features
  ↓
adjusted rating = strength_rating + host_advantage - travel_penalty + scenario_adjustment
  ↓
match probabilities using a Bradley-Terry-style win split + bounded draw probability
  ↓
group simulation using Monte Carlo
  ↓
tournament favourite proxy using rating softmax
```

Files:

```text
src/forecast_var/forecast_model.py
src/forecast_var/tools.py
```

Important limitation:

> The bundled ratings are demo priors. For a public prediction product, replace them with live ranking, Elo, squad, injury, lineup, weather, and schedule data.

---

## MCP implementation

The MCP server is here:

```text
mcp_servers/worldcup_forecast/server.py
```

It uses the Python MCP SDK's `FastMCP` server over stdio:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("worldcup_forecast", json_response=True)

@mcp.tool()
def forecast_match(team_a: str, team_b: str, adjustments: dict | None = None) -> dict:
    return tools.forecast_match(team_a, team_b, adjustments)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Tools exposed:

| Tool | Purpose |
|---|---|
| `validate_tournament_field` | Verify 48 teams and Italy absence |
| `get_source_registry` | Show active, placeholder, manual/paid, and disabled sources |
| `list_groups` | Return all 12 groups |
| `get_team_inputs` | Return demo feature row for a qualified team |
| `forecast_match` | Return 1X2 probabilities for a match |
| `forecast_group` | Simulate a group and return winner/top-two/top-three probabilities |
| `rank_teams` | Return demo tournament favourite ranking |
| `explain_model` | Explain model assumptions and limitations |

Why MCP matters:

- The model does not memorize football facts.
- The agent must call typed tools.
- Forecasting logic lives outside the LLM.
- Tool output includes citations, warnings, and scenario metadata.
- Read-only tools reduce safety and reproducibility risk.

---

## Live OpenAI API path

Offline mode is deterministic and free:

```bash
PYTHONPATH=src python scripts/run_agent.py "Who is favourite to win Group D?" --mode grounded_mock
```

Live mode uses the OpenAI Agents SDK with MCP:

```bash
export OPENAI_API_KEY="your_key_here"

PYTHONPATH=src python scripts/run_agent.py \
  "Who is favourite to win Group D and how certain is that?" \
  --mode openai \
  --model gpt-4.1-mini
```

The live path is implemented in:

```text
src/forecast_var/openai_agent.py
```

Engineering choices:

- `MCPServerStdio` launches the local MCP server as a subprocess.
- Static tool filtering exposes only approved read-only tools.
- `tool_choice="required"` forces tool use before answering.
- Strict schema conversion is enabled.
- Structured output is enforced through the `AgentAnswer` Pydantic schema.
- No LangChain, no Anthropic SDK, no hidden external scraping.

---

## Agent skills

Agent skills live in:

```text
.agents/skills/*/SKILL.md
```

Implemented skills:

| Skill | Purpose |
|---|---|
| `source-triage` | Select and disclose source status before forecasting |
| `forecast-modeling` | Use MCP forecast tools instead of guessing |
| `uncertainty-calibration` | Report probabilities and refuse fake certainty |
| `scenario-analysis` | Handle what-if injuries, suspensions, or rating shocks |
| `eval-review` | Audit tools, skills, citations, probabilities, and abstention |

Example:

```text
Can you guarantee Argentina will win the 2026 World Cup?
```

Expected behavior:

```text
Call rank_teams.
Report Argentina's model probability.
Refuse the guarantee.
Set abstained=true.
Explain uncertainty.
```

---

## Proper evaluation harness

The eval cases are in:

```text
data/eval/episode2_eval_cases.jsonl
```

The harness checks:

| Metric | Meaning |
|---|---|
| `pass_rate` | Fraction of cases passing every check |
| `tool_recall` | Required MCP tools used |
| `skill_recall` | Required skills selected |
| `citation_recall` | Claims grounded with citation IDs |
| `unsupported_claim_rate` | `1 - citation_recall` |
| `abstention_accuracy` | Correct refusal of certainty/guarantee questions |
| `probability_sanity_rate` | Forecast probabilities exist and are between 0 and 1 |

Run:

```bash
PYTHONPATH=src python scripts/evaluate.py --mode baseline_mock
PYTHONPATH=src python scripts/evaluate.py --mode grounded_mock
```

Expected result:

| Agent | Pass rate | Tool recall | Skill recall | Citation recall | Unsupported claim rate | Abstention accuracy | Probability sanity |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline mock | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | low | low |
| Grounded mock | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 |

---

## Forecast model backtest harness

A separate model audit is included:

```bash
PYTHONPATH=src python scripts/backtest_model.py
```

It computes:

```text
mean log loss
mean Brier score
per-match predicted probabilities
```

The bundled historical backtest is deliberately small. Its purpose is to show the right evaluation pattern, not to claim production-grade forecast quality.

---

## Run examples

### Validate the 48-team field

```bash
PYTHONPATH=src python scripts/validate_data.py
```

### Ask for sources

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "What sources can this agent use and which ones are disabled by default?" \
  --mode grounded_mock
```

### Forecast Group D

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Who is the favourite to win Group D and how certain is that?" \
  --mode grounded_mock
```

### Forecast a match

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Predict USA vs Australia and explain the main inputs." \
  --mode grounded_mock
```

### Refuse a fake guarantee

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Can you guarantee Argentina will win the 2026 World Cup?" \
  --mode grounded_mock
```

### Run a scenario

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "If France loses 80 rating points because of injuries, how does that change the top favourites?" \
  --mode grounded_mock
```

### Live OpenAI API run

```bash
export OPENAI_API_KEY="your_key_here"

PYTHONPATH=src python scripts/run_agent.py \
  "List the top 5 tournament favourites from the current demo model." \
  --mode openai \
  --model gpt-4.1-mini
```

### Run all checks

```bash
PYTHONPATH=src python scripts/validate_data.py
PYTHONPATH=src python scripts/evaluate.py --mode baseline_mock
PYTHONPATH=src python scripts/evaluate.py --mode grounded_mock
PYTHONPATH=src python scripts/backtest_model.py
PYTHONPATH=src python scripts/generate_figures.py
PYTHONPATH=src pytest -q
```

---

## Notebook

The executed notebook is:

```text
notebooks/02_forecast_var_prediction_agent.executed.ipynb
```

It tells the story end-to-end:

1. Why prediction agents are appealing and dangerous.
2. Validate the 48-team field and Italy absence.
3. Show the source registry.
4. Forecast Group D.
5. Produce top tournament favourites.
6. Run a France injury/rating-shock scenario.
7. Compare baseline vs grounded agent evaluation.
8. Show the backtest harness.
9. Explain how to run with live OpenAI APIs.

---

## Limitations and safety notes

- This is not betting advice.
- The bundled team priors are demo data, not official odds or rankings.
- A real forecast should refresh source adapters near publication time.
- Forecasts can be invalidated by squads, injuries, lineups, weather, red cards, tactical changes, and draw variance.
- A good prediction agent should be judged by calibration and transparency, not by one lucky pick.

---

## References

- FIFA World Cup 2026 tournament page: `https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026`
- Wikipedia 2026 FIFA World Cup: `https://en.wikipedia.org/wiki/2026_FIFA_World_Cup`
- FIFA/Coca-Cola World Rankings: `https://www.fifa.com/en/world-rankings`
- ClubElo API: `https://clubelo.com/API`
- OpenAI Agents SDK MCP docs: `https://openai.github.io/openai-agents-python/mcp/`
- MCP Python SDK: `https://github.com/modelcontextprotocol/python-sdk`

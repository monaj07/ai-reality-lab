# Football GenAI Reality Check: 2026 World Cup Grounded Agent

**Episode concept:** *I built a 2026 World Cup AI agent. Then I caught it lying.*

This is a compact, runnable repo for a football-themed GenAI reliability video. The theme is the 2026 FIFA World Cup, including the now-current tournament groups and a correction that matters for the episode: **Italy did not qualify for the 2026 World Cup and is not in any group.**

The repo compares two agents:

1. **Baseline agent** — answers confidently from “memory,” with no citations.
2. **Grounded agent** — retrieves from a local football fact base, cites every factual sentence, and abstains when evidence is missing.

The point is not to build another generic RAG tutorial. The point is to show a repeatable content format:

```text
Build the AI demo -> break the AI demo -> evaluate it -> fix it -> show the evidence
```

---

## v0.3 update: all 48 teams are now explicit

The fact base now includes the final 12 groups and all 48 teams, using FIFA-style team names.

| Group | Teams |
|---|---|
| A | Mexico, South Africa, Korea Republic, Czechia |
| B | Canada, Bosnia and Herzegovina, Qatar, Switzerland |
| C | Brazil, Morocco, Haiti, Scotland |
| D | USA, Paraguay, Australia, Türkiye |
| E | Germany, Curaçao, Côte d'Ivoire, Ecuador |
| F | Netherlands, Japan, Sweden, Tunisia |
| G | Belgium, Egypt, IR Iran, New Zealand |
| H | Spain, Cabo Verde, Saudi Arabia, Uruguay |
| I | France, Senegal, Iraq, Norway |
| J | Argentina, Algeria, Austria, Jordan |
| K | Portugal, Congo DR, Uzbekistan, Colombia |
| L | England, Croatia, Ghana, Panama |

The validator checks:

```text
12 groups
4 teams per group
48 total teams
48 unique teams
Italy is not in any group
```

Run it with:

```bash
PYTHONPATH=src python scripts/validate_groups.py
```

Expected output:

```json
{
  "group_count": 12,
  "team_count": 48,
  "unique_team_count": 48,
  "duplicate_teams": [],
  "groups_with_wrong_size": {},
  "italy_in_groups": false,
  "valid": true
}
```

---

## Agent engineering choices

This repo intentionally avoids LangChain, Anthropic SDKs and heavyweight orchestration frameworks.

It uses:

- Python
- OpenAI Python SDK / Responses API for live model calls
- function-tool pattern for retrieval
- strict structured JSON output schema
- deterministic guardrails before model calls
- deterministic evals after model calls
- deterministic mock backend for reproducible local demos without API spend

Practical agent-engineering standards implemented here:

| Standard | Implementation |
|---|---|
| Tool isolation | The model can only retrieve through `search_facts`. |
| Grounding first | The grounded agent retrieves local facts before answering. |
| Structured output | The live OpenAI path returns strict JSON with answer, citations, abstention and confidence. |
| Citation discipline | Every factual sentence must cite fact IDs like `[F015]`. |
| Abstention | Future predictions and unsupported claims are not invented. |
| Prompt-injection resistance | Obvious injection patterns trigger a local guardrail. |
| Eval-first workflow | Quality is measured with a dedicated eval harness. |
| Staleness checks | Current sports facts, such as final groups and non-qualified teams, are explicit eval cases. |
| Low complexity | The code is short enough to explain in a video. |

---

## Project structure

```text
football_genai_reality_check/
├── README.md
├── Makefile
├── requirements.txt
├── pyproject.toml
├── data/
│   ├── facts/world_cup_2026_facts.jsonl
│   ├── facts/world_cup_2026_groups.json
│   └── eval/world_cup_eval_set.jsonl
├── scripts/
│   ├── ask.py
│   ├── evaluate.py
│   └── validate_groups.py
├── src/wc_reality/
│   ├── facts.py
│   ├── groups.py
│   ├── guardrails.py
│   ├── schemas.py
│   ├── mock_agents.py
│   ├── openai_agent.py
│   └── eval.py
├── notebooks/
│   ├── 01_world_cup_agent_reality_check.ipynb
│   └── 01_world_cup_agent_reality_check.executed.ipynb
└── reports/
    ├── combined_eval_results.csv
    ├── combined_metric_summary.json
    ├── group_validation.json
    └── images/
```

---

## Data files

### `data/facts/world_cup_2026_groups.json`

Canonical local group list used by the validator.

### `data/facts/world_cup_2026_facts.jsonl`

Each row is a source-linked football fact:

```json
{
  "fact_id": "F015",
  "title": "2026 World Cup final groups and all 48 teams",
  "claim": "The final 2026 World Cup groups contain 48 teams: Group A - Mexico, South Africa, Korea Republic, Czechia; ...",
  "source_title": "FIFA: FIFA World Cup 26 standings and teams",
  "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/standings",
  "tags": ["2026", "final draw", "groups", "48 teams"],
  "aliases": ["final groups", "all 48 teams", "qualified teams", "Italy not in groups"]
}
```

The seed fact base covers:

- 2026 World Cup hosts and 48-team format
- 2026 tournament dates and 104-match structure
- final venue
- opening match
- all 12 groups and all 48 teams
- Australia’s Group D and first listed fixture
- Italy failing to qualify
- Argentina v France 2022 final facts
- a local grounding policy fact for prompt-injection tests

### `data/eval/world_cup_eval_set.jsonl`

Each row defines a test case:

```json
{
  "id": "q_all_48_teams",
  "question": "List all 48 teams in the final 2026 FIFA World Cup groups.",
  "gold_support_ids": ["F015"],
  "must_mention": ["Mexico", "South Africa", "Korea Republic", "Czechia", "..."],
  "should_abstain": false,
  "category": "answerable_all_48_teams"
}
```

The eval set includes:

- normal 2026 factual questions
- all-48-teams group-list validation
- Australia Group D questions
- Italy non-qualification questions
- unanswerable future questions
- a prompt-injection case

---

## Metrics

The eval harness calculates:

| Metric | Meaning |
|---|---|
| `citation_precision` | Whether cited facts are actually relevant. |
| `citation_recall` | Whether required support facts were cited. |
| `must_mention_recall` | Whether the answer includes required surface facts. |
| `unsupported_rate` | Factual sentences without valid citations. |
| `abstention_accuracy` | Whether the agent abstains only when it should. |
| `pass_rate` | Overall case pass/fail rate. |

The all-48-teams eval case requires **100% must-mention recall**.

Current deterministic mock results:

| Agent | Citation precision | Citation recall | Unsupported rate | Abstention accuracy | Pass rate | Cases |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 0.118 | 0.118 | 1.000 | 0.824 | 0.000 | 17 |
| Grounded | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 17 |

---

## Setup

```bash
cd football_genai_reality_check
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
cd football_genai_reality_check
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Run examples

### Validate all 48 teams

```bash
PYTHONPATH=src python scripts/validate_groups.py
```

### Ask for all final groups

```bash
PYTHONPATH=src python scripts/ask.py \
  "List all 48 teams in the final 2026 FIFA World Cup groups." \
  --agent grounded \
  --backend mock
```

### Ask whether Italy qualified

```bash
PYTHONPATH=src python scripts/ask.py \
  "Did Italy qualify for the 2026 FIFA World Cup?" \
  --agent grounded \
  --backend mock
```

Expected behavior: the agent says Italy failed to qualify and cites `[F013]` and `[F014]`.

### Ask which group Italy is in

```bash
PYTHONPATH=src python scripts/ask.py \
  "Which group is Italy in for the 2026 World Cup?" \
  --agent grounded \
  --backend mock
```

Expected behavior: the agent says Italy did not qualify, so Italy is not in any final group.

### Ask Australia's group

```bash
PYTHONPATH=src python scripts/ask.py \
  "Which teams are in Australia's 2026 World Cup group?" \
  --agent grounded \
  --backend mock
```

Expected behavior: USA, Paraguay, Australia and Türkiye.

### Ask a future-prediction question

```bash
PYTHONPATH=src python scripts/ask.py \
  "Who will win the 2026 FIFA World Cup?" \
  --agent grounded \
  --backend mock
```

Expected behavior: the agent abstains instead of inventing a winner.

### Run the full evaluation

```bash
PYTHONPATH=src python scripts/evaluate.py \
  --agent both \
  --backend mock \
  --out-dir reports
```

Or:

```bash
make eval
make validate-groups
```

---

## Run with the OpenAI SDK

The deterministic mock backend is best for recording the first episode. To test the live OpenAI path:

```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_MODEL="gpt-5.5"

PYTHONPATH=src python scripts/ask.py \
  "Did Italy qualify for the 2026 FIFA World Cup?" \
  --agent grounded \
  --backend openai
```

Evaluate the live OpenAI path:

```bash
PYTHONPATH=src python scripts/evaluate.py \
  --agent grounded \
  --backend openai \
  --model "$OPENAI_MODEL" \
  --out-dir reports_openai
```

---

## Episode storyboard

### Hook

Ask the baseline agent:

```text
Did Italy qualify for the 2026 FIFA World Cup?
```

It confidently says:

```text
Italy qualified for the 2026 World Cup and should be one of Europe's strongest teams.
```

Then show the eval result: **fail**.

### Build

Show the current fact records:

- `F013` — Italy failed to qualify.
- `F015` — all 48 final group-stage teams.
- `world_cup_2026_groups.json` — the group validator source.

### Reality check

Run:

```bash
PYTHONPATH=src python scripts/validate_groups.py
PYTHONPATH=src python scripts/evaluate.py --agent both --backend mock --out-dir reports
```

Show the metrics chart and pass/fail matrix.

### Takeaway

> Sports facts go stale fast. A demo tells you whether an AI system can answer. An eval tells you whether you should trust the answer.

---

## Limitations

This is a teaching repo, not a production sports-data product.

Known limitations:

- the fact base is curated and small
- retrieval is lexical, not vector/hybrid
- unsupported-claim detection is heuristic
- mock answers are intentionally scripted for an episode narrative
- live OpenAI outputs should be evaluated after each prompt/model/data change

---

## Good next episodes

1. **Data VAR:** review each AI claim like a football VAR decision.
2. **FootballBench:** build a harder benchmark of player, team and fixture ambiguity.
3. **Prompt Regression CI:** fail a GitHub pull request when prompt changes reduce answer quality.
4. **Live Source Update:** show how stale sports facts break AI systems.

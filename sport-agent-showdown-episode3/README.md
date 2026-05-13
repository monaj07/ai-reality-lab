# Episode 3 — Sport Agent Showdown

## Can one sports agent handle football, Formula 1 and chess without mixing facts?

This project is the third episode in a football/sport-themed GenAI reliability series. Instead of building yet another chatbot, we compare **agentic designs** on the same multi-sport benchmark.

The episode question is:

> **Which agent design works best for a sports assistant that needs to answer World Cup, F1 and chess questions with citations?**

The project is intentionally small and reproducible. It runs offline with deterministic mock agents, but it also includes an optional live implementation using the **OpenAI Agents SDK** and a local **MCP** server.

---

## Why this topic is engaging

Sports questions are deceptively difficult for AI agents:

- current facts change quickly, especially schedules, rankings and squads;
- names are ambiguous across sports and eras;
- users mix domains in one question;
- agents can confidently invent future results;
- older football players have incomplete or differently formatted statistics;
- official sources can differ by snapshot date.

This makes sports a good viewer-friendly way to explain serious agent engineering concepts.

---

## Agentic designs compared

| Design | Idea | Strength | Weakness |
|---|---|---|---|
| `single_agent` | One generalist answers everything | Simple and cheap | Confuses domains, weak tool discipline |
| `sequential_chain` | Route → retrieve → answer → verify | More reliable and readable | Rigid; still struggles with mixed questions |
| `triage_handoff` | Router delegates to football/F1/chess specialists | Best practical default | Needs good routing and merge logic |
| `committee_referee` | All specialists respond; referee validates and merges | Highest quality | More tool calls and higher cost |

The point is not that one design is universally best. The point is to measure trade-offs.

---

## What is implemented

```text
sport-agent-showdown-episode3/
  README.md
  AGENTS.md
  requirements.txt
  data/
    facts/
      football_worldcup_2026_groups.json
      football_legacy_players.json
      f1_2026_calendar_current.json
      f1_2026_original_calendar_note.json
      f1_2026_lineups.json
      chess_fide_may_2026_top_players.json
    rag/
      source_cards.jsonl
    eval/
      episode3_eval_cases.jsonl
    sources/
      source_registry.json
  .agents/skills/
    football-research/SKILL.md
    f1-research/SKILL.md
    chess-research/SKILL.md
    mixed-question-decomposition/SKILL.md
    uncertainty-calibration/SKILL.md
    citation-discipline/SKILL.md
    eval-review/SKILL.md
  mcp_servers/
    sport_knowledge/server.py
  src/sport_agent/
    schemas.py
    data.py
    rag.py
    router.py
    skills.py
    tools.py
    designs.py
    eval_harness.py
    openai_agents.py
  scripts/
    run_agent.py
    evaluate.py
    validate_data.py
    make_figures.py
  tests/
  notebooks/
```

---

## Data

The bundled data is a small **source-backed snapshot**, not a full sports database.

### Football

- FIFA World Cup 2026 final groups snapshot.
- Italy is deliberately absent from the World Cup field.
- Group D is USA, Paraguay, Australia and Türkiye.
- Historical player cards for Johan Cruyff and Michel Platini.

### Formula 1

- Current Formula1.com 2026 schedule snapshot.
- Formula1.com 2026 driver line-up snapshot.
- FIA original 2026 calendar announcement note.

The F1 calendar is intentionally useful for agent evaluation: one source card says the current Formula1.com snapshot lists 22 rounds, while the original FIA announcement said 24 races. A careful agent should mention the source/date difference.

### Chess

- FIDE May 2026 classical Top 100 snapshot, with the top 10 plus Gukesh D.
- Magnus Carlsen is rank 1 with rating 2840 in the bundled May 2026 source card.
- Gukesh D is included at rank 19 in the bundled snapshot.

---

## RAG design

This project uses **lightweight local RAG** instead of a vector database.

File:

```text
data/rag/source_cards.jsonl
```

Each card has:

```json
{
  "source_id": "fide_may_2026_top_players",
  "sport": "chess",
  "title": "FIDE Top 100 classical players, May 2026",
  "url": "https://ratings.fide.com/a_top.php",
  "retrieved_at": "2026-05-13",
  "text": "FIDE's May 2026 classical rating list ranks Magnus Carlsen first..."
}
```

Retrieval uses simple token scoring in `src/sport_agent/rag.py`. This keeps the episode easy to inspect. The RAG layer is exposed as the MCP tool `search_source_cards`.

---

## MCP implementation

The local MCP server is here:

```text
mcp_servers/sport_knowledge/server.py
```

It implements a minimal JSON-RPC stdio MCP server and exposes read-only tools:

```text
route_sport
search_source_cards
get_world_cup_group
get_f1_calendar
get_f1_driver_lineup
get_chess_top_players
compare_legacy_football_players
```

The flow is:

```text
Agent design
  ↓
MCP stdio client/server boundary
  ↓
Read-only tools over local source snapshots
  ↓
Structured answer with citations
  ↓
Evaluation harness
```

Why MCP here?

- It cleanly separates the model/agent layer from the data/tool layer.
- All designs use the same tool contract.
- The live OpenAI path can use the same server through `MCPServerStdio`.
- The offline deterministic path can call the same Python tool functions directly.

---

## Agent skills

Skills live in:

```text
.agents/skills/<skill-name>/SKILL.md
```

Skills are not data. They are procedural instructions. The router selects skills based on the question and design.

| Skill | Purpose |
|---|---|
| `football-research` | Handle World Cup, clubs, older players and future-result caution |
| `f1-research` | Handle driver line-ups, schedules and snapshot conflicts |
| `chess-research` | Handle ratings, titles and time-control distinctions |
| `mixed-question-decomposition` | Split multi-sport questions into sport-specific subtasks |
| `uncertainty-calibration` | Abstain on predictions, subjective rankings and future results |
| `citation-discipline` | Require source IDs and snapshot dates |
| `eval-review` | Judge outputs against expected tools, skills and citations |

---

## Evaluation harness

The eval cases are in:

```text
data/eval/episode3_eval_cases.jsonl
```

Each case defines:

```json
{
  "case_id": "mixed_weekend_briefing",
  "question": "Build me a mini sports briefing: World Cup Group D, the next F1 race, and the chess number one.",
  "expected_sports": ["football", "f1", "chess"],
  "expected_keywords": ["Group D", "USA", "Australia", "Canada", "Round 5", "Magnus Carlsen"],
  "required_tools": ["get_world_cup_group", "get_f1_calendar", "get_chess_top_players"],
  "required_skills": ["football-research", "f1-research", "chess-research", "mixed-question-decomposition", "citation-discipline"],
  "required_citations": ["fifa_wc26_final_groups", "f1_2026_calendar_current_formula1", "fide_may_2026_top_players"],
  "should_abstain": false
}
```

Metrics:

| Metric | Meaning |
|---|---|
| `pass_rate` | All checks passed |
| `route_accuracy` | Expected sports were detected |
| `tool_recall` | Required tools were used |
| `skill_recall` | Required skills were selected |
| `citation_recall` | Required source IDs were cited |
| `keyword_recall` | Expected facts appeared in the answer |
| `forbidden_absence` | Forbidden wrong claims did not appear |
| `abstention_accuracy` | The agent abstained when it should |
| `unsupported_claim_rate` | Cases with missing citations, forbidden facts or failed checks |
| `avg_tool_calls` | Efficiency proxy |
| `cost_proxy` | Rough cost proxy based on tools + design overhead |

---

## Setup

```bash
cd sport-agent-showdown-episode3
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Validate data

```bash
PYTHONPATH=src python scripts/validate_data.py
```

Expected output includes:

```json
{
  "valid": true,
  "world_cup_team_count": 48,
  "italy_in_world_cup": false,
  "f1_current_round_count": 22,
  "f1_lineup_team_count": 11,
  "chess_snapshot_count": 11
}
```

---

## Run one design

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Build me a mini sports briefing: World Cup Group D, the next F1 race, and the chess number one." \
  --design triage_handoff
```

Try the committee referee:

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "What is Magnus Carlsen's May 2026 FIDE rank, and which World Cup group is Argentina in?" \
  --design committee_referee
```

Try a future-result abstention case:

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Who won the 2026 FIFA World Cup?" \
  --design committee_referee
```

---

## Run evaluations

All designs:

```bash
PYTHONPATH=src python scripts/evaluate.py --design all
```

One design:

```bash
PYTHONPATH=src python scripts/evaluate.py --design triage_handoff
```

Reports are written to:

```text
reports/eval_<design>.jsonl
reports/summary_<design>.json
reports/summary_all_designs.csv
```

---

## Make figures

```bash
PYTHONPATH=src python scripts/make_figures.py
```

Figures:

```text
reports/figures/design_pass_rate.png
reports/figures/tool_cost_tradeoff.png
reports/figures/metric_radar_like.png
```

---

## Run tests

```bash
PYTHONPATH=src pytest -q
```

---

## Optional live OpenAI mode

Offline deterministic mode is the default. To test a live model with the same MCP server:

```bash
export OPENAI_API_KEY="your_key_here"

PYTHONPATH=src python scripts/run_agent.py \
  "Who drives for McLaren in the 2026 F1 season?" \
  --design openai_triage \
  --model gpt-4.1-mini
```

The live implementation is in:

```text
src/sport_agent/openai_agents.py
```

It uses:

- OpenAI Agents SDK
- `MCPServerStdio`
- static MCP tool filtering
- specialist handoffs for football, F1 and chess
- Pydantic structured output
- read-only local MCP tools

---

## Episode outline

Suggested title:

> **I Built One AI Sports Agent for Football, F1 and Chess — Then Tested 4 Agent Designs**

Story structure:

1. Start with a mixed question that a single agent mishandles.
2. Explain why sport is a good reliability testbed.
3. Introduce the four designs.
4. Show the same eval set run across all designs.
5. Highlight failures: Italy in World Cup, F1 calendar conflict, Gukesh rank, future World Cup winner.
6. Show the evaluation table and trade-off chart.
7. Conclude with the design recommendation.

Recommended conclusion:

> For a broad sports assistant, triage-handoff is the best default. Committee-referee is more reliable but more expensive. Single-agent is cheap but fragile. Sequential-chain is useful for simple workflows but weaker on mixed-domain questions.


---

## Final deterministic eval result

The project was executed in offline deterministic mode on 2026-05-13.

| design            |   pass_rate |   tool_recall |   skill_recall |   citation_recall |   abstention_accuracy |   unsupported_claim_rate |   avg_cost_proxy |
|:------------------|------------:|--------------:|---------------:|------------------:|----------------------:|-------------------------:|-----------------:|
| single_agent      |       0.000 |         0.100 |          0.793 |             0.489 |                 0.867 |                    0.667 |            1.350 |
| sequential_chain  |       0.933 |         1.000 |          1.000 |             1.000 |                 0.933 |                    0.000 |            2.052 |
| triage_handoff    |       1.000 |         1.000 |          1.000 |             1.000 |                 1.000 |                    0.000 |            2.584 |
| committee_referee |       1.000 |         1.000 |          1.000 |             1.000 |                 1.000 |                    0.000 |            4.208 |

Data validation and tests completed successfully:

```text
PYTHONPATH=src python scripts/validate_data.py
PYTHONPATH=src python scripts/evaluate.py --design all
PYTHONPATH=src python scripts/make_figures.py
PYTHONPATH=src pytest -q
```

Result:

```text
8 passed
```

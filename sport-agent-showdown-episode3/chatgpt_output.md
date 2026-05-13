Done — Episode 3 is now a full project.

# Episode 3: Sport Agent Showdown

**Core idea:**

> **Can one AI sports agent handle football, F1, and chess without mixing facts — and which agent design works best?**

This episode compares four agentic designs on the same sport benchmark:

1. `single_agent`
2. `sequential_chain`
3. `triage_handoff`
4. `committee_referee`

It covers football, Formula 1, and chess, including mixed questions like:

```text
Build me a mini sports briefing: World Cup Group D, the next F1 race, and the chess number one.
```

Project files:

[Download full project ZIP](sandbox:/mnt/data/sport-agent-showdown-episode3.zip)
[Open README.md](sandbox:/mnt/data/sport-agent-showdown-episode3/README.md)
[Open AGENTS.md](sandbox:/mnt/data/sport-agent-showdown-episode3/AGENTS.md)
[Open executed experiment notebook](sandbox:/mnt/data/sport-agent-showdown-episode3/notebooks/03_sport_agent_design_showdown.executed.ipynb)
[Open MCP server](sandbox:/mnt/data/sport-agent-showdown-episode3/mcp_servers/sport_knowledge/server.py)
[Open evaluation cases](sandbox:/mnt/data/sport-agent-showdown-episode3/data/eval/episode3_eval_cases.jsonl)
[Open final eval summary](sandbox:/mnt/data/sport-agent-showdown-episode3/reports/summary_all_designs.csv)

## What changed from Episode 2

This is **not another World Cup-only agent**. The project is now a broader **Sport Agent** that can handle:

```text
Football:
- World Cup 2026 groups
- Italy not being in the 2026 World Cup field
- legacy player comparisons such as Cruyff vs Platini

Formula 1:
- 2026 current schedule snapshot
- F1 driver line-ups
- calendar source conflicts

Chess:
- FIDE May 2026 classical ratings
- Carlsen/Gukesh ranking checks
```

The bundled current snapshots use FIFA’s final-draw/group source, Formula1.com’s current 2026 schedule page and 2026 line-up article, and FIDE’s May 2026 top-player list. Formula1.com’s current schedule snapshot lists Canada as Round 5 after Miami, while FIA’s earlier 2026 calendar announcement described a 24-race calendar, so the project deliberately includes that as a source-conflict test. ([FIFA][1])

## AGENTS.md

I used only:

```text
AGENTS.md
```

There is **no duplicate `Agents.md`**. That avoids conflicting instruction files across case-sensitive and case-insensitive filesystems. `AGENTS.md` is the standard dedicated instruction file pattern for coding agents. ([agents.md][2])

## MCP, skills, and RAG

The project uses all three, but in a deliberately lightweight way.

```text
Skills = sport-specific procedures
MCP = standard tool boundary
RAG = source-card retrieval
```

### MCP

The MCP server is here:

```text
mcp_servers/sport_knowledge/server.py
```

It exposes read-only tools:

```text
route_sport
search_source_cards
get_world_cup_group
get_f1_calendar
get_f1_driver_lineup
get_chess_top_players
compare_legacy_football_players
```

The optional live path uses OpenAI Agents SDK with `MCPServerStdio`, static tool filtering, specialist handoffs, required tool use, and Pydantic structured output. The OpenAI Agents SDK supports MCP server integration, stdio MCP servers, tool filtering, handoffs, and structured agent orchestration. ([OpenAI GitHub][3])

### Skills

Skills live here:

```text
.agents/skills/
```

Implemented skills:

```text
football-research
f1-research
chess-research
mixed-question-decomposition
uncertainty-calibration
citation-discipline
eval-review
```

### RAG

The lightweight source-card RAG file is:

```text
data/rag/source_cards.jsonl
```

No vector DB. No live scraping. It is intentionally readable for a video/tutorial episode.

## Evaluation result

Final deterministic offline run:

| Design              | Pass rate | Tool recall | Skill recall | Citation recall | Abstention accuracy | Unsupported claim rate | Avg cost proxy |
| ------------------- | --------: | ----------: | -----------: | --------------: | ------------------: | ---------------------: | -------------: |
| `single_agent`      |     0.000 |       0.100 |        0.793 |           0.489 |               0.867 |                  0.667 |          1.350 |
| `sequential_chain`  |     0.933 |       1.000 |        1.000 |           1.000 |               0.933 |                  0.000 |          2.052 |
| `triage_handoff`    |     1.000 |       1.000 |        1.000 |           1.000 |               1.000 |                  0.000 |          2.584 |
| `committee_referee` |     1.000 |       1.000 |        1.000 |           1.000 |               1.000 |                  0.000 |          4.208 |

The episode conclusion is clear:

> **Triage-handoff is the best default design for this Sport Agent. Committee-referee is equally accurate here, but costs more. Single-agent is too fragile for mixed sport questions.**

## Main commands

```bash
cd sport-agent-showdown-episode3

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Validate data:

```bash
PYTHONPATH=src python scripts/validate_data.py
```

Run one design:

```bash
PYTHONPATH=src python scripts/run_agent.py \
  "Build me a mini sports briefing: World Cup Group D, the next F1 race, and the chess number one." \
  --design triage_handoff
```

Compare all designs:

```bash
PYTHONPATH=src python scripts/evaluate.py --design all
```

Generate figures:

```bash
PYTHONPATH=src python scripts/make_figures.py
```

Run tests:

```bash
PYTHONPATH=src pytest -q
```

Live OpenAI mode:

```bash
export OPENAI_API_KEY="your_key_here"

PYTHONPATH=src python scripts/run_agent.py \
  "Who drives for McLaren in the 2026 F1 season?" \
  --design openai_triage \
  --model gpt-4.1-mini
```

The project ran successfully:

```text
8 passed
```

This episode is a good next step because it is no longer just “a sports chatbot.” It is an **agent-design comparison experiment** with a viewer-friendly sports theme.

[1]: https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/final-draw-results?utm_source=chatgpt.com "Final Draw results | FIFA World Cup 2026"
[2]: https://agents.md/?utm_source=chatgpt.com "AGENTS.md"
[3]: https://openai.github.io/openai-agents-python/mcp/ "Model context protocol (MCP) - OpenAI Agents SDK"

# Monte Carlo vs the OpenAI model

Forecast VAR uses two different kinds of intelligence:

```text
gpt-5.4-nano
= live agent model: routes, selects skills, calls MCP tools, explains and cites results

Python Monte Carlo simulator
= forecasting engine: samples tournament outcomes and produces probabilities
```

The LLM is not asked to invent champion probabilities. It calls MCP tools such as
`simulate_tournament`, `forecast_match_with_context`, and `forecast_group`. Those tools run
plain Python logic over validated tournament data and model inputs.

## Why this separation matters

A freehand LLM prediction can sound confident but is hard to audit. A tool-generated prediction can be:

- reproduced with the same code, inputs, parameters, and simulator seed,
- inspected in `src/forecast_var/tournament_sim.py`,
- compared against market baselines,
- checked for data gaps,
- evaluated for overclaiming.

This does not mean the live LLM API is bit-for-bit deterministic. Even with low temperature or seed controls, a hosted model can return slightly different wording, tool ordering, or reasoning traces across runs. Forecast VAR treats the LLM as the orchestrator and narrator, not as the source of the numeric prediction.

The reproducible part is the tool boundary: if `simulate_tournament` is called with the same bundled data, code version, simulation count, and seed, the Monte Carlo output should be the same. The auditable part is the recorded path around it: retrieved source cards, tool inputs, tool outputs, citations, typed claims, warnings, and claim-verification results. In the offline notebook, the deterministic mock agent makes the whole demo repeatable without live API calls.

## What Monte Carlo means here

The simulator runs many possible tournaments. Each match is sampled from model probabilities.
After all simulations finish, the code counts how often each team reaches a stage:

```text
champion probability = number of simulated titles / number of simulations
final probability    = number of simulated finals / number of simulations
semifinal probability = number of simulated semifinals / number of simulations
```

This is why Forecast VAR says things like:

```text
Argentina 21.0% champion probability
France 14.2% champion probability
```

rather than:

```text
Argentina will win.
```

## What gpt-5.4-nano does in live mode

When `--mode openai` is used, the OpenAI Agents SDK path defaults to `gpt-5.4-nano`.
The model should:

1. interpret the user question,
2. select relevant skills,
3. retrieve source cards,
4. call the pre-flight validation tool,
5. choose the correct forecast/simulation MCP tool,
6. explain the tool result,
7. include uncertainty and source caveats,
8. return the strict `AgentAnswer` schema.

The model should not:

- invent probabilities,
- guarantee future outcomes,
- present sample odds as betting advice,
- skip pre-flight validation,
- cite unsupported claims.

## What reproducibility means here

Forecast VAR uses "reproducible" in a narrow engineering sense:

```text
Reproducible:
- local RAG index build from bundled files
- source-card retrieval over that index
- Python forecast and Monte Carlo outputs when seeded
- evaluation metrics from deterministic mock agents

Not guaranteed bit-for-bit reproducible:
- live LLM wording
- live LLM intermediate reasoning
- exact live API orchestration if the hosted model changes
```

So the tool does not make the LLM itself deterministic. It makes the prediction-producing part deterministic and leaves an audit trail for the LLM-produced explanation.

## Episode teaching line

> The LLM is the presenter. The simulator is the stats department. MCP is the controlled phone line between them. The evaluation harness is the fact-checking desk.

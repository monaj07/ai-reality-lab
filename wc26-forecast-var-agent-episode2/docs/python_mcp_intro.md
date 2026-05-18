# Python MCP Intro

MCP, the Model Context Protocol, is a standard way to expose local or remote capabilities to AI clients as tools. In a Python project, an MCP server often wraps ordinary Python functions, gives them names and schemas, and makes them available to an MCP-capable client.

The key idea is simple:

```text
Python function
  -> registered as an MCP tool
  -> discovered by an AI client
  -> called by the client when the LLM decides it is useful
  -> result returned to the LLM
  -> final answer written in natural language
```

## Minimal Python Example

```python
from fastmcp import FastMCP

mcp = FastMCP("forecast-demo")

@mcp.tool()
def predict_match(team_a: str, team_b: str) -> dict:
    return {
        "winner": team_a,
        "confidence": 0.64,
    }

mcp.run()
```

After `mcp.run()` starts the server, an MCP-capable client can discover a tool named `predict_match`. The tool has a schema with two string arguments: `team_a` and `team_b`.

## What Happens At Runtime

The user does not usually type a Python call like this inside the AI client:

```python
predict_match("Brazil", "France")
```

Instead, the user asks in natural language:

```text
Who is more likely to win between Brazil and France?
```

The LLM and client decide whether a tool call is useful. If they choose the MCP tool, the client sends a structured request conceptually like:

```json
{
  "tool": "predict_match",
  "arguments": {
    "team_a": "Brazil",
    "team_b": "France"
  }
}
```

The MCP server executes the Python function and returns the result:

```json
{
  "winner": "Brazil",
  "confidence": 0.64
}
```

Then the LLM uses that result to write the final response:

```text
The tool estimates Brazil as more likely to win, with confidence 0.64.
```

## Division Of Responsibility

The MCP server does not interpret user prompts. It is not the agent brain.

The MCP server is responsible for:

- exposing tool names and schemas,
- validating tool arguments,
- executing the registered Python functions,
- returning structured results.

The AI client and LLM are responsible for:

- reading the user's prompt,
- deciding whether a tool should be used,
- choosing which tool to call,
- mapping natural language into tool arguments,
- using the returned result in the final answer.

## End-To-End Flow

```text
User prompt
  -> LLM reasons about the request
  -> LLM/client selects an MCP tool
  -> client sends structured arguments to the MCP server
  -> MCP server runs the Python function
  -> server returns structured output
  -> LLM writes the final answer
```

## Why This Matters

MCP is useful because it separates language understanding from execution. The LLM can decide that a forecast, database lookup, file search, or validation step is needed, but the actual work happens in deterministic, inspectable code.

That means a project can keep important logic inside Python tools while still giving users a natural-language interface.

## Common Misunderstanding

Running `mcp.run()` does not make the server understand prompts by itself. It only makes the registered tools available to clients.

Prompts are the trigger because the AI client and LLM translate user intent into tool calls. The MCP server only executes the requested tool call and returns the result.

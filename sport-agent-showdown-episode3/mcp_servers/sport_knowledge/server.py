#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sport_agent.tools import TOOL_FUNCTIONS  # noqa: E402


def tool_schema(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
    }


TOOLS = [
    tool_schema("route_sport", "Classify a question into football, f1, chess or unknown.", {"question": {"type": "string"}}, ["question"]),
    tool_schema("search_source_cards", "Search local source cards with simple RAG retrieval.", {"query": {"type": "string"}, "sport": {"type": "string"}, "top_k": {"type": "integer"}}, ["query"]),
    tool_schema("get_world_cup_group", "Look up 2026 World Cup groups by team or group letter.", {"team": {"type": "string"}, "group": {"type": "string"}}),
    tool_schema("get_f1_calendar", "Look up the current F1 2026 schedule snapshot.", {"round_number": {"type": "integer"}, "country": {"type": "string"}, "status": {"type": "string"}}),
    tool_schema("get_f1_driver_lineup", "Look up F1 2026 driver line-ups by team or driver.", {"team": {"type": "string"}, "driver": {"type": "string"}}),
    tool_schema("get_chess_top_players", "Look up the bundled May 2026 FIDE classical rating snapshot.", {"top_n": {"type": "integer"}, "player": {"type": "string"}}),
    tool_schema("compare_legacy_football_players", "Compare bundled legacy football player cards.", {"players": {"type": "array", "items": {"type": "string"}}}),
]


def ok_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error_result(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def content_result(payload: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}], "isError": False}


def handle(req: dict[str, Any]) -> dict[str, Any] | None:
    method = req.get("method")
    request_id = req.get("id")
    if method == "initialize":
        return ok_result(request_id, {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "sport-knowledge", "version": "0.1.0"}})
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return ok_result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = req.get("params", {})
        name = params.get("name")
        args = params.get("arguments") or {}
        func: Callable[..., Any] | None = TOOL_FUNCTIONS.get(name)
        if func is None:
            return error_result(request_id, -32602, f"Unknown tool: {name}")
        try:
            payload = func(**args)
        except Exception as exc:  # pragma: no cover
            return ok_result(request_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        return ok_result(request_id, content_result(payload))
    return error_result(request_id, -32601, f"Method not found: {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle(req)
        except Exception as exc:  # pragma: no cover
            resp = error_result(None, -32700, f"Parse/server error: {exc}")
        if resp is not None:
            print(json.dumps(resp, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

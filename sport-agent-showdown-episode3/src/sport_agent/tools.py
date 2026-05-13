from __future__ import annotations

from typing import Any

from . import data
from .rag import search_source_cards as rag_search
from .router import route_sports


def route_sport(question: str) -> dict[str, Any]:
    return {"sports": route_sports(question), "source_id": "router_heuristic"}


def search_source_cards(query: str, sport: str | None = None, top_k: int = 5) -> dict[str, Any]:
    cards = rag_search(query=query, sport=sport, top_k=top_k)
    return {"cards": cards, "source_ids": [c["source_id"] for c in cards]}


def get_world_cup_group(team: str | None = None, group: str | None = None) -> dict[str, Any]:
    wc = data.world_cup_groups()
    groups = wc["groups"]
    if group:
        key = group.upper().replace("GROUP", "").strip()
        return {"group": key, "teams": groups.get(key, []), "source_id": wc["source_id"]}
    if team:
        team_norm = team.lower().replace("turkiye", "türkiye")
        for g, teams in groups.items():
            for t in teams:
                if t.lower() == team_norm or t.lower().replace("ü", "u") == team.lower():
                    return {"team": t, "group": g, "teams": teams, "source_id": wc["source_id"]}
        return {"team": team, "group": None, "teams": [], "source_id": wc["source_id"], "note": f"{team} is not in the World Cup 2026 group snapshot."}
    return {"groups": groups, "source_id": wc["source_id"]}


def get_f1_calendar(round_number: int | None = None, country: str | None = None, status: str | None = None) -> dict[str, Any]:
    cal = data.f1_calendar()
    rounds = cal["rounds"]
    if round_number is not None:
        rounds = [r for r in rounds if r["round"] == round_number]
    if country:
        rounds = [r for r in rounds if country.lower() in r["country"].lower() or country.lower() in r["venue"].lower()]
    if status:
        rounds = [r for r in rounds if r["status"] == status]
    return {"rounds": rounds, "round_count": len(data.f1_calendar()["rounds"]), "source_id": cal["source_id"], "note": cal.get("note")}


def get_f1_driver_lineup(team: str | None = None, driver: str | None = None) -> dict[str, Any]:
    lineups = data.f1_lineups()
    teams = lineups["lineups"]
    if team:
        for t, drivers in teams.items():
            if team.lower() in t.lower() or t.lower() in team.lower():
                return {"team": t, "drivers": drivers, "source_id": lineups["source_id"]}
        return {"team": team, "drivers": [], "source_id": lineups["source_id"], "note": "Team not found."}
    if driver:
        for t, drivers in teams.items():
            if any(driver.lower() in d.lower() or d.lower() in driver.lower() for d in drivers):
                return {"driver": driver, "team": t, "drivers": drivers, "source_id": lineups["source_id"]}
        return {"driver": driver, "team": None, "drivers": [], "source_id": lineups["source_id"], "note": "Driver not found."}
    return {"lineups": teams, "source_id": lineups["source_id"]}


def get_chess_top_players(top_n: int = 5, player: str | None = None) -> dict[str, Any]:
    chess = data.chess_top_players()
    players = chess["players"]
    if player:
        matches = [p for p in players if player.lower() in p["display_name"].lower() or player.lower() in p["name"].lower()]
        return {"players": matches, "rating_list_month": chess["rating_list_month"], "time_control": chess["time_control"], "source_id": chess["source_id"]}
    return {"players": players[:top_n], "rating_list_month": chess["rating_list_month"], "time_control": chess["time_control"], "source_id": chess["source_id"]}


def compare_legacy_football_players(players: list[str] | None = None) -> dict[str, Any]:
    legacy = data.football_legacy_players()
    records = legacy["players"]
    if not players:
        players = list(records.keys())
    selected: dict[str, Any] = {}
    for requested in players:
        for name, rec in records.items():
            if requested.lower() in name.lower() or name.lower() in requested.lower():
                selected[name] = rec
    return {"players": selected, "source_id": legacy["source_id"]}


TOOL_FUNCTIONS = {
    "route_sport": route_sport,
    "search_source_cards": search_source_cards,
    "get_world_cup_group": get_world_cup_group,
    "get_f1_calendar": get_f1_calendar,
    "get_f1_driver_lineup": get_f1_driver_lineup,
    "get_chess_top_players": get_chess_top_players,
    "compare_legacy_football_players": compare_legacy_football_players,
}

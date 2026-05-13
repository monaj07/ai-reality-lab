from sport_agent.designs import run_design


def test_triage_handles_mixed_briefing():
    ans = run_design("Build me a mini sports briefing: World Cup Group D, the next F1 race, and the chess number one.", "triage_handoff")
    assert set(ans.sports) == {"football", "f1", "chess"}
    assert "get_world_cup_group" in ans.tools_used
    assert "get_f1_calendar" in ans.tools_used
    assert "get_chess_top_players" in ans.tools_used
    assert "Magnus Carlsen" in ans.answer


def test_committee_abstains_future_world_cup_winner():
    ans = run_design("Who won the 2026 FIFA World Cup?", "committee_referee")
    assert ans.abstained is True
    assert "cannot" in ans.answer.lower() or "not" in ans.answer.lower()


def test_f1_false_claim_corrected():
    ans = run_design("I heard Max Verstappen drives for Ferrari in 2026. Is that true?", "triage_handoff")
    assert "No" in ans.answer
    assert "Red Bull" in ans.answer
    assert "Charles Leclerc" in ans.answer

from sport_agent.eval_harness import evaluate_design, summarise


def test_committee_is_strongest_in_demo():
    seq = summarise(evaluate_design("sequential_chain"))
    committee = summarise(evaluate_design("committee_referee"))
    assert committee["pass_rate"] >= seq["pass_rate"]
    assert committee["citation_recall"] >= seq["citation_recall"]

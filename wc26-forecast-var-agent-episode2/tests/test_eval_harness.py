from forecast_var.eval_harness import evaluate
from forecast_var.mock_agent import run_baseline_mock, run_grounded_mock


def test_grounded_mock_passes_eval():
    result = evaluate(run_grounded_mock)
    assert result["summary"]["pass_rate"] == 1.0
    assert result["summary"]["citation_recall"] == 1.0
    assert result["summary"]["probability_sanity_rate"] == 1.0


def test_baseline_mock_fails_eval():
    result = evaluate(run_baseline_mock)
    assert result["summary"]["pass_rate"] < 0.5

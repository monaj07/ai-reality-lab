from forecast_var.eval_harness import evaluate
from forecast_var.mock_agent import run_grounded_mock, run_baseline_mock


def test_grounded_mock_passes_eval():
    summary = evaluate(run_grounded_mock)["summary"]
    assert summary["pass_rate"] == 1.0
    assert summary["preflight_recall"] == 1.0
    assert summary["source_support_precision"] == 1.0
    assert summary["unsupported_claim_rate"] == 0.0


def test_baseline_mock_fails_eval():
    summary = evaluate(run_baseline_mock)["summary"]
    assert summary["pass_rate"] == 0.0
    assert summary["preflight_recall"] == 0.0
    assert summary["source_support_precision"] == 0.0

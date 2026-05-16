from forecast_var.tools import verify_claims_against_sources


def test_claim_verifier_supports_model_claim():
    report = verify_claims_against_sources([
        {
            "text": "Argentina has a model-derived probability.",
            "claim_type": "model_output",
            "citation_ids": ["CITE-MODEL-FORECAST-VAR-V1", "CITE-SRC-SAMPLE-TEAM-PRIORS"],
        }
    ])
    assert report["source_support_precision"] == 1.0
    assert report["claims"][0]["supported"] is True


def test_claim_verifier_rejects_uncited_claim():
    report = verify_claims_against_sources([
        {"text": "This team will definitely win.", "claim_type": "model_output", "citation_ids": []}
    ])
    assert report["source_support_precision"] == 0.0
    assert report["claims"][0]["supported"] is False

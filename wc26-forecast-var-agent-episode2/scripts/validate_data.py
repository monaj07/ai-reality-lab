from __future__ import annotations

import json
from pathlib import Path

from forecast_var.data import all_teams, load_groups, load_team_features
from forecast_var.tools import preflight_forecast_context, validate_tournament_field

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    validation = validate_tournament_field()
    features = load_team_features()
    teams = all_teams()
    missing_features = [t for t in teams if t not in features]
    extra_features = [t for t in features if t not in teams]
    validation.update({
        "feature_rows": len(features),
        "missing_features": missing_features,
        "extra_features": extra_features,
        "groups": load_groups(),
        "preflight": preflight_forecast_context(),
    })
    validation["valid"] = validation["valid"] and not missing_features and not extra_features and validation["preflight"]["ready_for_forecast"]
    (PROJECT_ROOT / "reports").mkdir(exist_ok=True)
    with open(PROJECT_ROOT / "reports/data_validation.json", "w", encoding="utf-8") as f:
        json.dump(validation, f, ensure_ascii=False, indent=2)
    print(json.dumps(validation, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

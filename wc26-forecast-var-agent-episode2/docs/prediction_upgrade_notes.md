# Prediction-source upgrade notes

This upgrade keeps Forecast VAR self-contained while adding source-aware forecasting patterns:

- local evidence index,
- source adapters,
- rolling forecasts,
- market-baseline comparison,
- Brier/log-loss style evaluation,
- full-tournament simulation.

Forecast VAR keeps a different objective: it is an agent-engineering episode focused on MCP tools, skills, source governance, typed claims, and evaluation harnesses.

## What should improve prediction quality?

1. **Market baseline**: comparing model probabilities to de-vig odds can reveal when the model is far from a sample external baseline. De-vig means removing bookmaker margin by converting odds into implied probabilities and normalizing the outcomes to sum to 1.
2. **Rolling state**: completed results are locked, so the agent stops re-predicting what already happened.
3. **Curated evidence**: high-signal injury/suspension/tactical notes can be manually reviewed and injected.
4. **Historical calibration**: StatsBomb/OpenFootball-style historical data can help estimate upset/draw priors.
5. **Source coverage score**: the answer should disclose weak areas such as missing live lineups.

## What still should not be claimed?

- No forecast is certain.
- Demo priors are not official rankings.
- Sample market odds are not real live odds and are not betting advice.
- The Monte Carlo bracket is approximate, not an official FIFA bracket simulator.

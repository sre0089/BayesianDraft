# Availability

`bayesiandraft.simulation` includes a seeded baseline availability model.

## Purpose

Estimate whether a player is likely to remain available at the user's next pick or another target pick.

## Current Inputs

- Current `DraftState`
- Baseline `RankingRow` values
- Overall ADP
- Overall rank
- Recent position run signal
- A deterministic random seed

## Current Output

`AvailabilityEstimate` records:

- player ID
- target pick
- estimated probability
- simulation count
- seed

## Current Limitations

- This is a heuristic simulation, not a calibrated model.
- Opponent roster needs are simplified.
- Position-run effects are basic.
- Metrics such as Brier score, log loss, and calibration curves require historical draft data and are deferred.

# Modeling

BayesianDraft should use specialized models instead of one monolithic model.

## Model Families

- Player projections by position: QB, RB, WR, TE, K, D/ST.
- Injury and games-played model.
- Market and ADP model.
- Opponent selection model.
- Player availability model.
- Draft simulator.
- Season simulator.
- Candidate rollout optimizer.

## Principles

- Predict distributions, not only means.
- Use time-based validation.
- Avoid future leakage.
- Calibrate probabilities.
- Retain complex models only when they beat simpler baselines out of sample.
- Version every model artifact and input data snapshot.

Initial implementations should start with transparent baselines before advanced ML.

## Current Projection Baseline

Milestone 12 adds `bayesiandraft.projections`.

Current behavior:

- Builds `PlayerProjectionDistribution` records from validated snapshot projections.
- Carries season mean, median, floor, ceiling, games-played mean, model version, and data snapshot ID.
- Estimates weekly mean and weekly standard deviation from season-level projection quantiles.
- Samples non-negative weekly point outcomes from explicit seeds.

Current limitations:

- This is a transparent baseline, not a trained model.
- Distribution shape is normal with a zero floor.
- Position-specific model features, historical training, and calibration are deferred.

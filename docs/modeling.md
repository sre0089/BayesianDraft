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

# Recommendations

Milestone 8 implements a deterministic baseline recommendation engine.

## Inputs

- Current `DraftState`
- Baseline `RankingRow` values
- Available-player set
- Primary user roster counts

## Score Components

```text
TotalScore =
  VORP
  + PositionNeed
  + TierScore
  + MarketScore
  - Penalty
```

Current components:

- `value_score`: points over replacement from baseline rankings.
- `need_score`: starter vacancy boost for QB, RB, WR, TE, K, and DST.
- `tier_score`: boost for higher-tier players.
- `market_score`: boost when ADP is later than model rank.
- `penalty`: early K/DST and duplicate K/DST penalty.
- `next_pick_availability`: simple ADP and pick-distance heuristic.
- Availability model support exists in `bayesiandraft.simulation`, but the baseline recommendation engine still uses a lightweight inline heuristic until recommendation orchestration is wired to the simulator.
- `confidence`: deterministic heuristic derived from score shape.

## Output

The engine returns:

- primary recommendation
- top alternatives
- total score
- component scores
- confidence
- estimated next-pick availability
- explanation bullets

## Candidate Rollout Optimizer

Milestone 15 adds `optimize_candidates`.

Current behavior:

- Requires the primary user to be on clock.
- Evaluates a configurable pool of available candidates.
- Records each candidate as the user's pick in a copied draft state.
- Runs seeded remaining-draft simulations.
- Ranks candidates by rollout VORP with lightweight draft-value context.
- Returns a primary optimized candidate, alternatives, rollout summaries, and explanations.

## Current Limitations

- Availability is a heuristic, not a calibrated probability model.
- Candidate rollout uses the current heuristic draft simulator.
- Opponent personalization is a first-pass profile heuristic, not a calibrated model.
- Recommendation utility is not yet tied to season simulation or championship probability.

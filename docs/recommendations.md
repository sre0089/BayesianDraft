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

## Current Limitations

- Availability is a heuristic, not a calibrated probability model.
- No Monte Carlo rollout is included yet.
- No opponent personalization is included yet.
- Recommendation utility is not yet tied to season simulation or championship probability.

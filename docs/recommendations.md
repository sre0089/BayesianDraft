# Recommendations

BayesianDraft includes a deterministic baseline recommendation engine.

## Inputs

- Current `DraftState`
- Baseline `RankingRow` values
- Available-player set
- Primary user roster counts

## Score Components

```text
TotalScore =
  VORP
  + DynamicPositionNeed
  + TierScore
  + TierDropScore
  + MarketScore
  + NextPickRiskScore
  - Penalty
```

Current components:

- `value_score`: points over replacement from baseline rankings.
- `draft_phase`: early, middle, or late based on the current draft round.
- `need_score`: starter vacancy boost weighted by draft phase. It includes configured Flex slots once base eligible-position needs are filled. It matters less early and more later.
- `tier_score`: boost for higher-tier players.
- `tier_drop_score`: boost when few same-position players remain in the candidate's tier.
- `market_score`: boost when ADP is later than model rank.
- `next_pick_risk_score`: boost when the player is unlikely to make it back to the configured user's next pick.
- `penalty`: early K/DST and duplicate K/DST penalty.
- `next_pick_availability`: simple ADP and pick-distance heuristic.
- Availability model support exists in `bayesiandraft.simulation`, but the baseline recommendation engine still uses a lightweight inline heuristic until recommendation orchestration is wired to the simulator.
- `confidence`: deterministic heuristic derived from score shape. This is retained in the model output for now, but it is not calibrated and should not be treated as a probability.

## Output

The engine returns:

- primary recommendation
- top alternatives
- total score
- component scores
- draft phase
- confidence
- estimated next-pick availability
- explanation bullets

The CLI also groups recommendations by positions the configured user roster still needs. Each group shows up to five available players ranked by the same recommendation score for that position. For the configured `FLEX` slot, eligible RB/WR/TE groups stay open after the base RB/WR/TE starters are filled until the Flex requirement is covered.

## Candidate Rollout Optimizer

`optimize_candidates` evaluates draft candidates with seeded rollout summaries.

Current behavior:

- Requires the configured user manager to be on clock.
- Seeds the candidate pool with top options from positions the configured user roster still needs, then fills remaining slots by overall rank.
- Records each candidate as the user's pick in a copied draft state.
- Runs seeded remaining-draft simulations.
- Ranks candidates by rollout VORP with lightweight draft-value context.
- Returns a primary optimized candidate, alternatives, rollout summaries, and explanations.

In the CLI, this appears as a best-path comparison. The best-now recommendation is the immediate additive score; the best-path rollout is the simulated roster path after taking a candidate and letting the rest of the draft play out.

## Export

Use the export command to write recommendation snapshots:

```bash
PYTHONPATH=. python scripts/export_recommendations.py --out /tmp/recommendations.json --scenario data/fixtures/rehearsal_user_pick_8.json
```

This exports baseline recommendation JSON for a fresh draft state, optionally after applying a rehearsal scenario.

## Current Limitations

- Availability is a heuristic, not a calibrated probability model.
- Candidate rollout uses the current heuristic draft simulator.
- Opponent personalization is a first-pass profile heuristic, not a calibrated model.
- Recommendation utility is not yet tied to season simulation or championship probability.

# Recommendations

BayesianDraft's recommendation engine is intentionally transparent. It does not just print the top ranked player; it scores each available player against the current draft state and shows why the top option makes sense.

## Inputs

The baseline engine uses:

- the current `DraftState`
- available players
- baseline `RankingRow` values
- the configured user's roster
- optional path-bank context

## Score Shape

The current score is additive:

```text
TotalScore =
  VORP
  + DynamicPositionNeed
  + TierScore
  + TierDropScore
  + OpportunityCostScore
  + MarketScore
  + NextPickRiskScore
  - Penalty
```

The point of this shape is not to hide the decision behind a model. Each part maps to something you would naturally think about during a draft:

- `value_score`: how much projected value the player adds over replacement.
- `need_score`: how much the pick helps your current roster construction, including Flex.
- `tier_score`: how strong the player's current tier is.
- `tier_drop_score`: how close that position is to a tier cliff.
- `opportunity_cost_score`: how much worse the expected later option is at the same position, when a path bank is loaded.
- `market_score`: whether ADP suggests the market is letting the player fall.
- `next_pick_risk_score`: how unlikely the player is to reach your next pick.
- `penalty`: timing penalties, mainly for early K/DST picks and duplicate low-flexibility roster construction.

The CLI shows this as a compact breakdown, for example:

```text
need +24.5 | value +90.2 | tier +24.0 | opp +8.4 | risk +17.6 | market +1.2 | penalty 0.0
```

## What The Recommendation Means

The primary recommendation is the best current pick according to the live board and your roster. It is not meant to be followed blindly. It is meant to give you a defensible starting point:

- If the recommendation has high `value` and high `risk`, the player is strong and probably will not come back.
- If `need` is doing most of the work, the engine is protecting roster construction.
- If `opp` is high, the path bank thinks waiting at that position gets expensive.
- If `market` is positive, the model likes the player more than the ADP market does.

## Position Groups

The TUI also shows recommendations by positions your roster still needs. This is useful when the best overall player and the best strategic direction are not obviously the same thing.

For each open position group, the engine lists up to five available players using the same scoring components. For Flex, RB/WR/TE remain open after base starters are filled until the Flex requirement is covered.

## Path-Bank Context

When a path bank is loaded, the engine can compare:

```text
take this position now
vs
expected best same-position option at your next pick
```

This is what lets the tool reason about opportunity cost. For example, it can prefer a high-value QB over a need-based RB if saved paths suggest a useful RB is usually still available later. It can also push RB harder when the saved paths show the RB tier is likely to collapse before your next pick.

## Candidate Rollouts

`optimize_candidates` is the heavier candidate comparison path. It:

1. Requires the configured user manager to be on the clock.
2. Picks a candidate pool from needed positions and top overall players.
3. Records each candidate as the user's current pick in a copied draft state.
4. Simulates the rest of the draft with seeded paths.
5. Ranks candidates by the resulting roster value.

In practice, the baseline recommendation answers "who is best right now?" while rollout analysis asks "what does my roster tend to look like if I take this player now?"

## Export

Export recommendation snapshots with:

```bash
PYTHONPATH=. python scripts/export_recommendations.py \
  --out /tmp/recommendations.json \
  --scenario data/fixtures/rehearsal_user_pick_8.json
```

## Current Limits

- Availability is still a heuristic, not a calibrated probability model.
- Opponent behavior is based on simple draft profiles.
- Candidate rollout depends on the current draft simulator.
- The recommendation score does not yet optimize playoff or championship probability directly.

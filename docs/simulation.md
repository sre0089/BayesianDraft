# Simulation

Simulation must be reproducible from explicit seeds.

## Draft Simulation

The draft simulator should simulate remaining picks conditional on the current draft state, opponent behavior, roster needs, ADP distributions, and position runs.

Current implementation:

- `simulate_remaining_draft` rolls forward from a `DraftState` until the draft is complete or the ranked player pool is exhausted.
- `simulate_candidate_rollout` records a user pick, simulates the remaining draft repeatedly, and summarizes the user's resulting roster value.
- `analyze_league_paths` runs many full-draft paths and aggregates manager projected points, VORP, median outcome, volatility, average finish, top-three rate, and first-place rate.
- `analyze_user_strategy_paths` forces the user's next pick by position and compares how each early-position path performs after the rest of the draft is simulated.
- `DraftSimulationConfig` controls simulation count, seed, ADP spread, roster-need weight, and candidate pool size.
- Remaining-draft simulation uses first-pass opponent profiles inferred from completed picks.
- All stochastic paths are seeded and reproducible.

## Multi-Path Draft Analysis

Multi-path analysis answers a broader draft-day question than a single recommendation: if the current draft continues in many plausible ways, which teams usually end up strongest and which first-pick strategy gives the user the best final roster distribution?

The standalone report script can run heavier analysis from a fresh snapshot, a rehearsal state, or a saved live draft:

```bash
PYTHONPATH=. python scripts/analyze_draft_paths.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --draft-state data/processed/live_draft_state.json \
  --simulations 500
```

For a scratch rehearsal that jumps to the configured user pick:

```bash
PYTHONPATH=. python scripts/analyze_draft_paths.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --auto-pick-to-user \
  --simulations 500
```

The report format is intentionally compact:

```text
After 500 simulated draft paths:

Manager Results
1. Team 04      avg VORP   312.4   avg pts  2870.2   avg finish  2.1
2. Your Team    avg VORP   298.8   avg pts  2835.7   avg finish  3.0

Your Strategy Outcomes
RB early path   avg VORP   304.2   avg pts  2860.5   top3   42%
WR early path   avg VORP   296.8   avg pts  2824.1   top3   38%

Risk
Best case:   338.5 VORP
Median:      299.2 VORP
Worst:       241.0 VORP
Volatility:   22.8
Top 3 rate:   41%
Win rate:     13%
```

The CLI `Simulation` tab uses the same analysis code with a smaller path count so it remains responsive while entering picks live.

Current limitations:

- Opponent behavior is still heuristic and only uses the current draft.
- The fixture player pool is intentionally small, so fixture simulations stop when ranked players run out.
- Draft-path analysis compares roster strength using projection and VORP totals, not full weekly schedule outcomes.
- Candidate rollout and path analysis do not yet estimate playoff or championship probability.

## Season Simulation

The season simulator should sample weekly player outcomes, account for injuries and byes, optimize legal lineups, simulate matchups, determine playoff qualification, and simulate playoffs.

Current implementation:

- `optimize_lineup` fills fixed starting slots and configured flex slots from weekly player scores.
- `simulate_weekly_lineup` samples weekly projection outcomes for a roster and returns the optimized lineup.
- `simulate_roster_season` repeats weekly lineup simulation across a configured week range and summarizes total and average points.
- All weekly sampling uses explicit seeds.

Current limitations:

- This is a roster points simulator, not a full league schedule simulator.
- Matchups, standings, playoff qualification, and playoff brackets are deferred.
- Bye weeks, waiver moves, lineup locks, and injury-week availability are not integrated yet.

Runtime, cache behavior, and seed reproducibility must be measured and tested.

## Benchmark Smoke Check

Use the benchmark smoke check:

```bash
PYTHONPATH=. python scripts/sim_benchmark.py
```

This reports elapsed time and completion metadata for a seeded remaining-draft smoke simulation.

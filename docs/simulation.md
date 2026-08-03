# Simulation

Simulation must be reproducible from explicit seeds.

## Draft Simulation

The draft simulator should simulate remaining picks conditional on the current draft state, opponent behavior, roster needs, ADP distributions, and position runs.

Current implementation:

- `simulate_remaining_draft` rolls forward from a `DraftState` until the draft is complete or the ranked player pool is exhausted.
- `simulate_candidate_rollout` records a user pick, simulates the remaining draft repeatedly, and summarizes the user's resulting roster value.
- `DraftSimulationConfig` controls simulation count, seed, ADP spread, roster-need weight, and candidate pool size.
- Remaining-draft simulation uses first-pass opponent profiles inferred from completed picks.
- All stochastic paths are seeded and reproducible.

Current limitations:

- Opponent behavior is still heuristic and only uses the current draft.
- The fixture player pool is intentionally small, so fixture simulations stop when ranked players run out.
- Candidate rollout summarizes projected points and VORP, but does not yet estimate playoff or championship probability.

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

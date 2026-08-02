# Simulation

Simulation must be reproducible from explicit seeds.

## Draft Simulation

The draft simulator should simulate remaining picks conditional on the current draft state, opponent behavior, roster needs, ADP distributions, and position runs.

Current implementation:

- `simulate_remaining_draft` rolls forward from a `DraftState` until the draft is complete or the ranked player pool is exhausted.
- `simulate_candidate_rollout` records a user pick, simulates the remaining draft repeatedly, and summarizes the user's resulting roster value.
- `DraftSimulationConfig` controls simulation count, seed, ADP spread, roster-need weight, and candidate pool size.
- All stochastic paths are seeded and reproducible.

Current limitations:

- Opponent behavior is still heuristic.
- The fixture player pool is intentionally small, so fixture simulations stop when ranked players run out.
- Candidate rollout summarizes projected points and VORP, but does not yet estimate playoff or championship probability.

## Season Simulation

The season simulator should sample weekly player outcomes, account for injuries and byes, optimize legal lineups, simulate matchups, determine playoff qualification, and simulate playoffs.

Runtime, cache behavior, and seed reproducibility must be measured and tested.

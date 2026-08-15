# Simulation

Simulation is used for two jobs in BayesianDraft:

1. Estimate what might still be available later.
2. Compare draft paths instead of judging one pick in isolation.

All stochastic simulation paths use explicit seeds, so a run can be reproduced from the same state and config.

## Draft Simulation

The draft simulator starts from a `DraftState` and rolls forward until the draft is complete or the ranked player pool runs out.

Current pieces:

- `simulate_remaining_draft`: simulates the rest of the draft from the current state.
- `simulate_candidate_rollout`: records a user pick, runs remaining-draft simulations, and summarizes the resulting user roster.
- `analyze_league_paths`: runs many full-draft paths and compares manager outcomes.
- `analyze_user_strategy_paths`: samples possible boards at the user's next pick, forces a next-pick position, and compares final roster outcomes.
- `score_roster_strength`: scores teams by best legal starting lineup plus discounted positive bench value.
- `DraftSimulationConfig`: controls simulation count, seed, ADP spread, roster-need weight, and candidate pool size.

Opponent behavior is still heuristic. The simulator uses first-pass opponent profiles inferred from completed picks, but it is not trying to perfectly predict every manager.

## Multi-Path Draft Analysis

Multi-path analysis is useful when you want a bigger-picture read:

- Which managers tend to finish strongest from this board?
- Which next-pick position tends to produce the best final roster?
- What does the user's best/median/worst outcome look like?

Run the standalone report from a saved live draft:

```bash
PYTHONPATH=. python scripts/analyze_draft_paths.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --draft-state data/processed/live_draft_state.json \
  --simulations 500
```

For a rehearsal that jumps to the configured user pick:

```bash
PYTHONPATH=. python scripts/analyze_draft_paths.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --auto-pick-to-user \
  --simulations 500
```

Example output:

```text
After 500 simulated draft paths:

Manager Results
1. Team 04      avg VORP   312.4   avg pts  2870.2   avg finish  2.1
2. Your Team    avg VORP   298.8   avg pts  2835.7   avg finish  3.0

Your Strategy Outcomes
Next pick RB    avg VORP   304.2   avg pts  2860.5   top3   42%
Next pick WR    avg VORP   296.8   avg pts  2824.1   top3   38%

Risk
Best case:   338.5 VORP
Median:      299.2 VORP
Worst:       241.0 VORP
Volatility:   22.8
Top 3 rate:   41%
Win rate:     13%
```

The TUI `Simulation` tab uses the same analysis code with a smaller run size so it stays responsive.

## Path Bank

A path bank is a precomputed draft cache. Instead of rerunning thousands of deep simulations during the draft, BayesianDraft can look up similar saved paths and quickly estimate:

- player availability by pick
- expected positional value by pick
- positional drop-off by pick

Build it before the draft:

```bash
PYTHONPATH=. python scripts/build_path_bank.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --simulations 10000 \
  --out data/processed/path_bank_2026.json
```

Inspect it:

```bash
PYTHONPATH=. python scripts/inspect_path_bank.py data/processed/path_bank_2026.json
```

Load it into the TUI:

```bash
PYTHONPATH=. python scripts/draft_tui.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --path-bank data/processed/path_bank_2026.json
```

During a live draft, the TUI updates path-bank opportunity-cost context after each pick without rerunning the full simulation. Exact saved paths are used when possible, similar paths are used when the real draft diverges, and the full bank is used as a fallback.

## Season Simulation

The season simulator samples weekly player outcomes and optimizes legal lineups.

Current pieces:

- `optimize_lineup`: fills fixed starting slots and Flex slots from weekly player scores.
- `simulate_weekly_lineup`: samples weekly projection outcomes and returns the optimized lineup.
- `simulate_roster_season`: repeats weekly lineup simulation across a week range.

Current limits:

- It is a roster-points simulator, not a full league schedule simulator.
- Matchups, standings, playoff qualification, and playoff brackets are not wired in yet.
- Bye weeks, waiver moves, lineup locks, and week-specific injury availability are not fully integrated yet.

## Benchmark Smoke Check

Use the benchmark smoke check when you want a quick runtime sanity test:

```bash
PYTHONPATH=. python scripts/sim_benchmark.py
```

It prints elapsed time and completion metadata for a seeded remaining-draft simulation.

## Current Limits

- Opponent behavior is heuristic.
- Fixture simulations can stop early because the public fixture player pool is small.
- Draft-path analysis uses projected best-lineup value and discounted bench value, not full schedule outcomes.
- Candidate rollout and path analysis do not yet estimate playoff or championship probability.

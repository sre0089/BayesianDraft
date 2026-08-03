# Product Spec

BayesianDraft is a local-first fantasy football draft assistant for configurable ESPN-style full-PPR redraft leagues.

The product optimizes draft decisions rather than static player rankings. Recommendations should account for the live draft state, the user's roster, opponent rosters, player projections, positional scarcity, market cost, future pick positions, availability probability, and downstream roster outcomes.

## Primary Modes

- Draft Room: live manual draft tracking, recommendations, draft board, rosters, save/load, undo/redo.
- Rankings: model rankings, positional rankings, tiers, ADP comparisons, sleeper/fade views, uncertainty indicators.
- Simulator: mock drafts, strategy comparisons, candidate comparisons, locked picks, seeded exports.

## Initial League

- Platform: ESPN
- Format: 14-team redraft
- Scoring: full PPR
- Draft type: snake
- Draft date: August 8, 2026
- User draft slot: 8

The public repository uses anonymized manager labels. Real manager names should stay out of committed config and docs.

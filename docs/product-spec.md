# Product Spec

BayesianDraft is a local-first fantasy football draft assistant for Primary User's private 12-team ESPN full-PPR redraft league.

The product optimizes draft decisions rather than static player rankings. Recommendations should account for the live draft state, the user's roster, opponent rosters, player projections, positional scarcity, market cost, future pick positions, availability probability, and downstream roster outcomes.

## Primary Modes

- Draft Room: live manual draft tracking, recommendations, draft board, rosters, save/load, undo/redo.
- Rankings: model rankings, positional rankings, tiers, ADP comparisons, sleeper/fade views, uncertainty indicators.
- Simulator: mock drafts, strategy comparisons, candidate comparisons, locked picks, seeded exports.

## Initial League

- Platform: ESPN
- Format: 12-team redraft
- Scoring: full PPR
- Draft type: snake
- Draft date: August 8, 2026
- User draft slot: 9

See `BayesianDraft_Project_Specification_FULL.md` for complete requirements.

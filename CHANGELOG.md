# Changelog

All notable project changes will be documented here.

## Unreleased

- Initialized source-of-truth project and engineering workflow documents.
- Started Milestone 0 repository foundation.
- Added documentation skeleton, backend package foundation, frontend scaffold, league config, and CI.
- Added PyYAML-backed league config loading and validation.
- Implemented configurable fantasy scoring for passing, rushing, receiving, kicking, and D/ST.
- Implemented deterministic snake draft state with rosters, availability, undo/redo, edit, and save/load.
- Added core data schema records for players, teams, games, stats, projections, ADP, injuries, draft state, recommendations, simulations, and snapshots.
- Added a synthetic baseline player snapshot, manifest, loader, and offline validation tests.
- Added transparent baseline rankings with VORP, value above starter, tiers, ADP deltas, sleeper/fade scores, and JSON/CSV export.
- Added local FastAPI endpoints for league config, players, rankings, draft state, picks, rosters, undo/redo, and save/load.
- Added a browser-local manual draft room with search, position filters, draft board, roster view, undo/redo, and save/restore.
- Added explainable baseline recommendations in the backend, API, and draft room UI.
- Updated the league setup to a public-safe 14-team draft with the primary user in slot 8.
- Added a seeded baseline availability model for next-pick survival estimates.
- Added seeded remaining-draft simulation and candidate rollout summaries.
- Added ingestion manifest validation, checksum verification, and a baseline manifest verifier.
- Added baseline projection distributions and seeded weekly projection sampling.
- Added injury-aware games-played estimates with risk labels and explanations.
- Added weekly lineup optimization and seeded roster season simulation.
- Added candidate rollout optimization and a local API endpoint for candidate rollouts.

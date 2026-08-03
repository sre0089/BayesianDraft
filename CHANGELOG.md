# Changelog

All notable project changes will be documented here.

## Unreleased

- Added documentation, backend package foundation, frontend scaffold, league config, and CI.
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
- Added a browser-local candidate rollout simulator panel to the draft room.
- Added first-pass opponent draft profiles and simulator pick bias by manager preference.
- Added a safe dry-run ESPN integration boundary with environment-based configuration.
- Added historical backtesting metric helpers for rank error, Brier score, and log loss.
- Added draft-day preflight checks and CLI output for local readiness validation.
- Added local post-draft decision audit records and JSON persistence helpers.
- Added local model registry metadata helpers and active-model lookup.
- Added local data refresh hooks that verify ingestion manifests without external fetches.
- Added OpenAPI schema export and contract tests for key API endpoints.
- Added build metadata helpers, a version CLI, and a local API version endpoint.
- Added draft rehearsal scenarios and a CLI preview for repeatable mock-draft states.
- Added a draft-day runbook and local validation aggregator command.
- Added a league sanity report for draft setup and non-blocking config warnings.
- Added a snapshot health report for projection, ADP, and injury coverage.
- Added a recommendation export script for baseline draft-board snapshots.
- Added a draft state summary helper and CLI for compact draft-room review.
- Added a roster balance report for positional starter gaps and surplus.
- Added a simulator benchmark smoke check for seeded draft rollouts.
- Added a repo privacy scan command for public-safe manager-name checks.
- Added a documentation index and local link check for docs navigation.
- Added a local CI helper that gathers Python, API, and web checks.
- Removed internal planning artifacts from the public repository.

# Scripts

These are small command-line helpers for local development and draft-day prep. Most commands expect to be run from the repo root with `PYTHONPATH=.`.

## Draft Room

- `draft_tui.py`: launches the interactive terminal draft room.
- `draft_summary.py`: prints a compact JSON summary of a draft state.
- `rehearsal_preview.py`: loads a rehearsal scenario and prints the resulting state.
- `roster_balance.py`: shows roster needs and surplus for a manager.

## Data

- `import_snapshot.py`: imports a user-provided projection CSV into a validated snapshot.
- `pull_dynastyprocess.py`: pulls public DynastyProcess/FantasyPros ranking data into a local snapshot.
- `pull_fantasypros_projections.py`: pulls FantasyPros projections when an API key is available.
- `snapshot_health.py`: checks player, projection, ADP, and injury coverage for a snapshot.
- `verify_ingestion_manifest.py`: verifies checksum metadata for imported data.
- `data_refresh.py`: runs local refresh hooks that do not require live services.

## Rankings And Recommendations

- `export_baseline_rankings.py`: exports the current baseline board to JSON or CSV.
- `export_recommendations.py`: exports the current recommendation set.

## Simulation

- `build_path_bank.py`: precomputes draft paths for faster live opportunity-cost estimates.
- `inspect_path_bank.py`: prints path-bank metadata and coverage.
- `analyze_draft_paths.py`: runs heavier draft-path and next-pick strategy analysis.
- `sim_benchmark.py`: smoke test for seeded draft rollout speed.

## Maintenance

- `preflight.py`: draft-day readiness checks.
- `league_report.py`: validates and summarizes the league config.
- `privacy_scan.py`: catches real manager names in tracked-facing text.
- `check_docs_index.py`: checks local Markdown links in `docs/README.md`.
- `validate_local.py`: runs a few local readiness commands.
- `ci_local.py`: runs the broader Python and web validation set.
- `export_openapi.py`: writes the API schema.
- `version_info.py`: prints build/version metadata.

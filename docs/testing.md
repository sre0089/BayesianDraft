# Testing

The test suite is meant to keep draft-day behavior boring and predictable. Small documentation changes do not need every check, but anything touching draft state, recommendations, scoring, simulation, data loading, or the UI should get real coverage.

## Test Types

- Unit: scoring, draft order, roster legality, rankings, recommendation components, serialization.
- Integration: API workflows, draft entry, undo/redo, save/load, frontend/backend interaction.
- Simulation: reproducibility, legal picks, legal lineups, probability sanity checks, runtime.
- Failure: missing data, stale data, duplicate picks, invalid player IDs, sync failure, restart recovery.

Tests should use fixtures instead of live services. Live data pulls belong in scripts, not unit tests.

## Draft-Day Preflight

Run the draft-day preflight with:

```bash
PYTHONPATH=. python scripts/preflight.py
PYTHONPATH=. python scripts/preflight.py --json
```

The preflight checks validate league config, player snapshot, ingestion manifest checksum, save directory availability, and ESPN credential status.

## Local Validation Aggregator

Run the local validation aggregator with:

```bash
PYTHONPATH=.:apps/api/src python scripts/validate_local.py
```

This command runs the local preflight, data refresh verification, rehearsal preview, and version metadata checks.

## League Sanity Report

Run the league sanity report with:

```bash
PYTHONPATH=. python scripts/league_report.py
```

This prints the validated league setup, draft size, user draft position, and non-blocking config warnings.

## Recommendation Roster Audit

Run sampled drafts where the configured user manager blindly follows the model's top recommendation:

```bash
PYTHONPATH=. python scripts/audit_model_roster_completion.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --drafts 10 \
  --seed 91 \
  --candidate-limit 250
```

This reports whether the final user roster covers every configured starter and Flex requirement.

## Privacy Scan

Run the privacy scan with:

```bash
PYTHONPATH=. python scripts/privacy_scan.py
```

This fails when real draft manager names appear as standalone words in committed text files.

## Docs Index Check

Run the docs index check with:

```bash
PYTHONPATH=. python scripts/check_docs_index.py
```

This verifies that links in `docs/README.md` point to existing local Markdown files.

## Local CI Helper

Run the local CI helper with:

```bash
PYTHONPATH=.:apps/api/src python scripts/ci_local.py --list
PYTHONPATH=.:apps/api/src python scripts/ci_local.py
```

This gathers the Python, API, and web checks that are worth running before pushing larger changes.

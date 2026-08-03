# Testing

Testing should scale with risk and milestone scope.

## Test Types

- Unit: scoring, draft order, roster legality, rankings, recommendation components, serialization.
- Integration: API workflows, draft entry, undo/redo, save/load, frontend/backend interaction.
- Simulation: reproducibility, legal picks, legal lineups, probability sanity checks, runtime.
- Failure: missing data, stale data, duplicate picks, invalid player IDs, sync failure, restart recovery.

Tests must use fixtures instead of live services.

## Draft-Day Preflight

Milestone 20 adds:

```bash
PYTHONPATH=. python scripts/preflight.py
PYTHONPATH=. python scripts/preflight.py --json
```

The preflight checks validate league config, player snapshot, ingestion manifest checksum, save directory availability, and ESPN credential status.

## Local Validation Aggregator

Milestone 27 adds:

```bash
PYTHONPATH=.:apps/api/src python scripts/validate_local.py
```

This command runs the local preflight, data refresh verification, rehearsal preview, and version metadata checks.

## League Sanity Report

Milestone 28 adds:

```bash
PYTHONPATH=. python scripts/league_report.py
```

This prints the validated league setup, draft size, user draft position, and non-blocking config warnings.

## Privacy Scan

Milestone 34 adds:

```bash
PYTHONPATH=. python scripts/privacy_scan.py
```

This fails when real draft manager names appear as standalone words in committed text files.

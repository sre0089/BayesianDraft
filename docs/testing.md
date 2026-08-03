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

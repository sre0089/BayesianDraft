# Testing

Testing should scale with risk and milestone scope.

## Test Types

- Unit: scoring, draft order, roster legality, rankings, recommendation components, serialization.
- Integration: API workflows, draft entry, undo/redo, save/load, frontend/backend interaction.
- Simulation: reproducibility, legal picks, legal lineups, probability sanity checks, runtime.
- Failure: missing data, stale data, duplicate picks, invalid player IDs, sync failure, restart recovery.

Tests must use fixtures instead of live services.

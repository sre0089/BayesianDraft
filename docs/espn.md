# ESPN Integration

Milestone 18 adds a safe ESPN integration boundary.

## Current Behavior

- Loads optional ESPN settings from environment variables.
- Reports whether credentials are configured.
- Supports a dry-run sync result.
- Defines normalized draft-pick and sync-result records.

## Current Limitations

- No live ESPN network calls are performed.
- Real credentials must never be committed.
- Player and manager ID reconciliation is deferred until live API behavior is validated.

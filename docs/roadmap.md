# Roadmap

The reliable draft-day product comes first. Advanced projections, personalized opponent models, and ESPN synchronization should improve the local manual workflow without making it brittle.

## Current Capabilities

- Configuration-driven full-PPR scoring and draft settings.
- Deterministic snake draft state with rosters, availability, undo/redo, edits, and save/load.
- Synthetic baseline player snapshot with manifest validation and export tooling.
- Baseline rankings, explainable recommendations, and seeded availability estimates.
- Seeded draft simulations, candidate rollouts, roster balance reports, and rehearsal scenarios.
- Local FastAPI service and browser-based draft room.
- Dry-run ESPN integration boundary, preflight checks, privacy scan, docs index check, and local CI helper.

## Near-Term Work

- Improve the draft room for live use: faster player entry, clearer recommendation states, and stronger keyboard flows.
- Replace synthetic fixtures with reproducible public or user-provided projection snapshots.
- Expand recommendation evaluation with historical draft and season backtests.
- Add safer session persistence for draft-day recovery.

## Later Work

- Validate projection distributions against real historical outcomes.
- Add personalized opponent models from user-provided draft history.
- Add opt-in ESPN sync once the manual workflow is dependable.
- Convert draft recommendations into season-level playoff and championship probability estimates.

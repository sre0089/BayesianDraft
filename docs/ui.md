# UI

BayesianDraft's UI should prioritize draft-day speed, clear state, and manual reliability.

## Draft Room Requirements

- Current round
- Current overall pick
- Manager on clock
- Picks until the user's next pick
- Primary recommendation
- Available-player table
- Search
- Position filters
- Manual pick entry
- Undo and redo
- Draft board
- User roster
- Save and restore
- Data freshness and sync status when available

## Implemented Manual Draft Room Slice

Milestone 7 adds a browser-local draft room in `apps/web`.

Implemented:

- Current round, overall pick, manager on clock, and next user pick.
- Baseline recommendation band.
- Available-player table.
- Search and position filters.
- Manual draft action.
- Recent-picks draft board.
- Primary user roster panel.
- Undo and redo.
- Browser-local save and restore.
- Recommendation explanation bullets.
- Candidate rollout simulator panel when the primary user is on clock.

## Current Limitations

- The UI uses synthetic fixture-derived data embedded in the frontend.
- It does not yet call the FastAPI backend.
- Edit-prior-pick UI is deferred.
- Autosave and keyboard shortcuts are deferred.
- Recommendation and rollout explanations are baseline heuristics, not calibrated simulation outputs.

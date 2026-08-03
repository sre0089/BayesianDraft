# Draft Engine

The draft-state engine models a deterministic 14-team snake draft.

Required domain concepts:

- Manager
- Player
- DraftPick
- Roster
- DraftState
- LeagueConfig

Required behavior:

- Current round, overall pick, round pick, and manager on clock.
- the user's future picks.
- Record pick.
- Remove drafted player from availability.
- Add drafted player to manager roster.
- Undo, redo, and edit prior picks.
- Save, load, serialize, and restore.

State transitions must be deterministic and fully testable.

## Implemented API

Milestone 2 implements the initial backend draft-state engine in `bayesiandraft.draft`:

- `Player`
- `DraftPick`
- `Roster`
- `PickSlot`
- `DraftState`
- `pick_slot_for_overall_pick`
- `default_total_rounds`
- `build_rosters`

## Implemented Behavior

- Deterministic 14-team snake order.
- Current overall pick, round, round pick, and manager on clock.
- Future user picks.
- Manual pick recording with manager-on-clock validation.
- Duplicate player rejection.
- Unknown player rejection.
- Roster updates with positional counts.
- Available-player tracking.
- Undo and redo.
- Prior-pick editing.
- JSON save/load round trip.
- Complete mock draft entry through backend logic.
- Rehearsal scenarios that apply scripted fixture picks to reach repeatable draft states.

## Rehearsal

Milestone 26 adds:

```bash
PYTHONPATH=. python scripts/rehearsal_preview.py
```

The default scenario advances the fixture draft to pick 8 so the primary user is on clock.

## Current Assumption

Draft length is derived from starting slots plus bench slots. IR is excluded from draft length. A future milestone may add an explicit `draft_rounds` field to league configuration if the actual draft room differs.

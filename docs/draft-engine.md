# Draft Engine

The draft-state engine models a deterministic 12-team snake draft.

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

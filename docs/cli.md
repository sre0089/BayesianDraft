# Interactive CLI

BayesianDraft includes a keyboard-driven terminal UI for testing the draft engine without running the web app.

Launch with the built-in fixture:

```bash
PYTHONPATH=. python scripts/draft_tui.py
```

The CLI starts at pick 1 by default. During a live draft, select the drafted player and press Enter or `d`; the pick is recorded for whichever manager is currently on clock. Rankings, recommendations, rosters, and availability update immediately after each pick. Draft, undo, redo, and auto-pick actions autosave by default.
The Summary view opens as a compact dashboard with status, the current best overall recommendation, roster, recent-pick, version, and snapshot context.

Start directly at the pick-8 rehearsal scenario only when you want a quick local demo:

```bash
PYTHONPATH=. python scripts/draft_tui.py \
  --scenario data/fixtures/rehearsal_user_pick_8.json
```

Use an imported snapshot:

```bash
PYTHONPATH=. python scripts/draft_tui.py \
  --snapshot data/processed/my_snapshot.json
```

Use the latest pulled public rankings snapshot:

```bash
PYTHONPATH=. python scripts/pull_dynastyprocess.py
PYTHONPATH=. python scripts/draft_tui.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json
```

Use `--scenario` only with snapshots that contain the player IDs referenced by that scenario. The built-in pick-8 scenario is designed for the built-in synthetic fixture.

For rehearsal runs where you want BayesianDraft to simulate the early picks and jump directly to your configured draft slot, add:

```bash
PYTHONPATH=. python scripts/draft_tui.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --auto-pick-to-user
```

Run a heavier path analysis report outside the interactive UI:

```bash
PYTHONPATH=. python scripts/analyze_draft_paths.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --draft-state data/processed/live_draft_state.json \
  --simulations 500
```

For a scratch rehearsal report that jumps directly to your configured draft slot:

```bash
PYTHONPATH=. python scripts/analyze_draft_paths.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --auto-pick-to-user \
  --simulations 500
```

## Views

- `Summary`: current pick, manager on clock, available player count, roster size, save status, next user pick, Draft Assistant readout, and best-now recommendation. The Draft Assistant shows a live quick direction that updates after every pick from the current board, plus cached deep-simulation guidance when it is still fresh.
- `Rankings`: scrollable available-player table, match count, pick preview, and selected-player detail when the terminal is wide enough. Press `/` or start typing while on Rankings to filter immediately.
- `Recommendations`: best overall recommendation, live positional groups, score breakdown, stale/fresh path-analysis status, and top five available players for each position your roster still needs.
- `Managers`: yazi-style manager browser with every competitor roster, pick count, projected points, VORP, and position counts.
- `Roster`: configured user manager roster and positional starter needs.
- `Health`: snapshot coverage and warnings.
- `Simulation`: multi-path draft analysis showing simulated manager results, draft strategy analysis for your next pick, and risk summary. Press `a` to start the analysis from inside the TUI; the run log updates during the league-path phase and the next-pick strategy phase. When the board changes after analysis, the view marks the results stale, but Summary still keeps its quick direction live without rerunning the deep simulation.
- `Picks`: recent completed picks.

## Controls

| Key | Action |
| --- | --- |
| Left / Right | Move between views |
| Up / Down | Move ranking selection or manager selection; rankings scroll with the highlighted row |
| Page Up / Page Down | Move through rankings or managers in larger jumps |
| Home / End | Jump to the first or last ranking or manager |
| Enter or `d` | Draft the selected player |
| `/` | Start live search; typed characters filter immediately and show match count |
| Type on Rankings | Start live search without pressing `/` |
| Enter or Esc | Finish live search |
| Backspace | Remove the last live-search character |
| `[` / `]` | Cycle positional ranking filters |
| `0` | Show all positions |
| `1` through `6` | Jump to QB, RB, WR, TE, DST, or K |
| `c` | Clear search and positional filter |
| `u` | Undo last pick |
| `r` | Redo pick |
| `s` | Save draft state |
| `a` | Run multi-path analysis when the Simulation view is active |
| `?` | Toggle in-app help for controls and score definitions |
| `q` or Esc | Quit |

By default, autosave and pressing `s` write to `data/processed/cli_draft_state.json`. Override it with:

```bash
PYTHONPATH=. python scripts/draft_tui.py --save-path /tmp/my-draft.json
```

Disable autosave for rehearsal runs with:

```bash
PYTHONPATH=. python scripts/draft_tui.py --no-autosave
```

Resume from the save path if it exists:

```bash
PYTHONPATH=. python scripts/draft_tui.py --load-save
```

Write accepted-pick audit events with recommendation context:

```bash
PYTHONPATH=. python scripts/draft_tui.py --audit-path data/processed/decision_audit.json
```

## Notes

- The CLI records picks for whichever manager is currently on clock.
- Use the `Managers` view during the draft to audit every competitor roster as picks are entered.
- Recommendations always evaluate the configured user manager's roster.
- The UI uses the same ranking, recommendation, simulation, and roster-balance engine code as the export scripts.

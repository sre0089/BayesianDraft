# Interactive CLI

BayesianDraft includes a keyboard-driven terminal UI for testing the draft engine without running the web app.

Launch with the built-in fixture:

```bash
PYTHONPATH=. python scripts/draft_tui.py
```

The CLI starts at pick 1 by default. During a live draft, select the drafted player and press Enter or `d`; the pick is recorded for whichever manager is currently on clock. Rankings, recommendations, rosters, and availability update immediately after each pick.
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

## Views

- `Summary`: current pick, manager on clock, available player count, roster size, next user pick, and the live best overall recommendation.
- `Rankings`: scrollable available-player table and selected-player detail when the terminal is wide enough.
- `Recommendations`: best overall recommendation plus top five available players for each position your roster still needs.
- `Managers`: yazi-style manager browser with every competitor roster, pick count, and position counts.
- `Roster`: configured user manager roster and positional starter needs.
- `Health`: snapshot coverage and warnings.
- `Simulation`: seeded remaining-draft benchmark metadata.
- `Picks`: recent completed picks.

## Controls

| Key | Action |
| --- | --- |
| Left / Right | Move between views |
| Up / Down | Move ranking selection or manager selection; rankings scroll with the highlighted row |
| Enter or `d` | Draft the selected player |
| `/` | Start live search; typed characters filter immediately |
| Enter or Esc | Finish live search |
| Backspace | Remove the last live-search character |
| `[` / `]` | Cycle positional ranking filters |
| `0` | Show all positions |
| `1` through `6` | Jump to QB, RB, WR, TE, DST, or K |
| `c` | Clear search and positional filter |
| `u` | Undo last pick |
| `r` | Redo pick |
| `s` | Save draft state |
| `q` or Esc | Quit |

By default, pressing `s` writes to `data/processed/cli_draft_state.json`. Override it with:

```bash
PYTHONPATH=. python scripts/draft_tui.py --save-path /tmp/my-draft.json
```

## Notes

- The CLI records picks for whichever manager is currently on clock.
- Use the `Managers` view during the draft to audit every competitor roster as picks are entered.
- Recommendations always evaluate the configured user manager's roster.
- The UI uses the same ranking, recommendation, simulation, and roster-balance engine code as the export scripts.

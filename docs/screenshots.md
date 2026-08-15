# Screenshot Guide

The README is ready for screenshots, but the images should be captured from a clean local run instead of mocked.

## Where To Put Images

Use this folder:

```text
docs/assets/
```

Recommended filenames:

- `tui-summary.png`
- `tui-rankings.png`
- `tui-recommendations.png`
- `tui-managers.png`
- `web-draft-room.png`

## What To Capture

### TUI Summary

Show the main decision panel with:

- current pick
- best overall recommendation
- score breakdown
- quick direction
- roster sidebar

Command:

```bash
PYTHONPATH=. python scripts/draft_tui.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --path-bank data/processed/path_bank_2026.json
```

### TUI Rankings

Show the rankings tab with a few positions visible and the selected-row styling.

Good things to include:

- player names on the left
- position-colored stat columns
- selected player highlight
- ADP delta column

### TUI Recommendations

Show the recommendations tab with:

- best overall recommendation
- positional recommendation groups
- score breakdown
- path-bank context, if loaded

### TUI Managers

Show the manager browser with:

- manager list
- projected points
- VORP
- selected manager roster

### Web Draft Room

If the web app is included in the README, capture the main draft-room screen after:

```bash
npm run dev
```

## README Snippet

After screenshots are added, use a short section like this near the top of `README.md`:

```md
## Screenshots

![BayesianDraft TUI summary](docs/assets/tui-summary.png)

![BayesianDraft rankings view](docs/assets/tui-rankings.png)
```

Keep the README to two or three screenshots. Put extra images in docs if needed.

## Privacy Check

Before committing screenshots:

- use anonymized manager names
- avoid private league IDs
- avoid API keys, terminal history, email addresses, or local paths outside the repo
- run `PYTHONPATH=. python scripts/privacy_scan.py`

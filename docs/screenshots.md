# Screenshot Guide

The README uses a small set of real TUI screenshots captured from a local run.

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

The README should stay limited to the clearest two or three screenshots:

```md
## Screenshots

![BayesianDraft TUI summary](docs/assets/tui-summary.png)

![BayesianDraft rankings view](docs/assets/tui-rankings.png)
```

Put extra images in docs if needed.

## Current Images

![BayesianDraft TUI summary](assets/tui-summary.png)

![BayesianDraft rankings view](assets/tui-rankings.png)

![BayesianDraft recommendations view](assets/tui-recommendations.png)

## Privacy Check

Before committing screenshots:

- use anonymized manager names
- avoid private league IDs
- avoid API keys, terminal history, email addresses, or local paths outside the repo
- run `PYTHONPATH=. python scripts/privacy_scan.py`

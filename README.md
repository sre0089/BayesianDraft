# BayesianDraft

BayesianDraft is a local-first fantasy football draft assistant. It is built for a live snake draft where you enter picks as they happen and the tool keeps updating the board, roster needs, and recommendation logic.

The main idea is simple: rankings are useful, but draft decisions depend on context. A good pick should account for who is still available, what your roster needs, what might make it back to you, where the market is discounting players, and how different paths could affect the final roster.

## What It Does

- Tracks a full snake draft with manual pick entry, undo/redo, save/load, and roster views.
- Ranks available players using projections, VORP, tiers, ADP, roster need, and availability risk.
- Explains recommendations with a compact score breakdown instead of just giving a name.
- Shows position-aware recommendations so you can compare the best QB/RB/WR/TE paths.
- Runs seeded draft simulations and path-bank analysis for faster draft-day context.
- Provides both a terminal draft room and a small local web/API surface.

## Why I Built It

Most draft tools are either static rankings or mock draft rooms. BayesianDraft is closer to a live decision assistant: it tries to answer “what should I do from this exact board state?” after every pick.

It is intentionally local-first. You can use public or user-provided projection data, keep your actual league details out of git, and run the whole workflow from your machine.

## Quick Start

Install Python and Node dependencies:

```bash
pip install -e ".[dev]"
npm install
```

Run the terminal draft room with the included fixture data:

```bash
PYTHONPATH=. python scripts/draft_tui.py
```

The fixture data is synthetic, so it is mainly for testing the flow. To use real player data, import or pull a snapshot first.

Pull a public DynastyProcess snapshot:

```bash
PYTHONPATH=. python scripts/pull_dynastyprocess.py
```

Then run the TUI with that snapshot:

```bash
PYTHONPATH=. python scripts/draft_tui.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json
```

For faster live recommendations, build a path bank ahead of time:

```bash
PYTHONPATH=. python scripts/build_path_bank.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --simulations 10000 \
  --out data/processed/path_bank_2026.json

PYTHONPATH=. python scripts/draft_tui.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --path-bank data/processed/path_bank_2026.json
```

## Using The TUI

The terminal UI starts at pick 1. Enter every pick as it happens, including picks before your slot. The recommendation panel updates after each pick.

Useful controls:

- Arrow keys: move between players, tabs, and manager views
- Enter or `d`: draft the selected player for whoever is on the clock
- `/`: live search
- `[` and `]`: cycle position filters
- `u` / `r`: undo and redo
- `s`: save
- `q`: quit

More details are in [docs/cli.md](docs/cli.md).

Screenshots are not committed yet. The capture checklist is in [docs/screenshots.md](docs/screenshots.md) so the README images can be added from a clean local run.

## Local League Names

The public config uses anonymized manager labels. If you want your local TUI to show real names, create:

```text
configs/leagues/espn_2026.local.yaml
```

That file is ignored by git. `scripts/draft_tui.py` will use it automatically when it exists.

## Project Layout

- `bayesiandraft/`: core Python package for draft state, scoring, rankings, recommendations, simulations, data loading, and audits.
- `apps/api/`: local FastAPI app.
- `apps/web/`: React/Vite draft room.
- `configs/`: public-safe league configuration.
- `data/`: synthetic fixtures plus ignored raw/processed/snapshot folders.
- `docs/`: architecture, CLI, methodology, data, and model notes.
- `scripts/`: import, validation, simulation, export, and draft-room commands.
- `tests/`: Python unit tests plus web/API tests under their app folders.

## Methodology

The technical writeup lives in [docs/math-methodology.md](docs/math-methodology.md). It covers VORP, tier pressure, roster need, ADP value, next-pick availability, simulation paths, and how those pieces feed the recommendation score.

Short version: the current engine is intentionally transparent. It uses deterministic scoring plus seeded simulations so recommendations can be inspected, tested, and reproduced.

## Development Checks

Python:

```bash
pytest
ruff check .
mypy bayesiandraft apps/api/src scripts
PYTHONPATH=. python scripts/privacy_scan.py
```

Web:

```bash
npm test
npm run lint
npm --workspace apps/web run build
```

Local API:

```bash
uvicorn bayesiandraft_api.main:app --app-dir apps/api/src --reload
```

Web app:

```bash
npm run dev
```

## Data And Privacy

BayesianDraft is designed to keep real league data local. Do not commit private league exports, API keys, ESPN cookies, local draft saves, raw downloaded datasets, or real manager names.

The repo includes a privacy scan and `.gitignore` rules for common local artifacts, but it is still worth checking `git status --ignored` before publishing anything.

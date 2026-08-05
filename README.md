# BayesianDraft

BayesianDraft is a local-first probabilistic fantasy football draft assistant for configurable fantasy football leagues.

Most fantasy tools rank players. BayesianDraft ranks decisions. The target product recommends the available player who maximizes expected final roster strength, and eventually playoff and championship probability, given the live draft state.

## What It Does

- Tracks a snake draft with manual picks, rosters, availability, undo/redo, and save/restore.
- Scores players with configuration-driven full-PPR league settings.
- Builds baseline rankings from projections, replacement levels, ADP, tiers, and risk signals.
- Explains recommendations with roster needs, player value, scarcity, and next-pick availability.
- Runs seeded draft simulations and candidate rollouts for repeatable strategy comparison.
- Keeps ESPN integration behind a dry-run boundary so local manual mode stays reliable.

## Tech Stack

- Backend: Python 3.12, FastAPI, Pydantic, Polars, DuckDB or SQLite
- Frontend: React, TypeScript, Vite, Vitest, React Testing Library
- Testing: pytest, Ruff, mypy where practical, Vitest
- Modeling: scikit-learn first, CatBoost/LightGBM only when validated
- Storage: local configuration, data snapshots, draft sessions, model artifacts, and audit logs

## Repository Layout

- `bayesiandraft/`: scoring, draft state, rankings, recommendations, simulation, data, modeling, and audit logic.
- `apps/api/`: local FastAPI service for the draft room and supporting tooling.
- `apps/web/`: browser-based draft room UI.
- `configs/`: league settings and anonymized draft configuration.
- `data/`: committed fixtures plus ignored raw, processed, and snapshot data directories.
- `docs/`: public product, architecture, data, modeling, and API notes.
- `scripts/`: local validation, export, preflight, and reporting commands.

## Technical Methodology

The engine methodology is documented in [docs/math-methodology.md](docs/math-methodology.md), including draft-state notation, VORP, tiering, recommendation scoring, availability simulation, candidate rollouts, lineup simulation, and validation metrics.

## Local Data Import

User-provided projection CSVs can be converted into validated snapshot JSON with:

```bash
PYTHONPATH=. python scripts/import_snapshot.py --players path/to/projections.csv --out data/processed/my_snapshot.json --season 2026 --source "user-provided"
```

The CSV contract and privacy guidance are documented in [docs/data-import.md](docs/data-import.md).

Imported snapshots can be passed to local commands with `--snapshot` or to the API with `BAYESIANDRAFT_PLAYER_SNAPSHOT_PATH`.

Pull public DynastyProcess/FantasyPros rankings into a local snapshot:

```bash
PYTHONPATH=. python scripts/pull_dynastyprocess.py
```

Then launch the CLI with real player names:

```bash
PYTHONPATH=. python scripts/draft_tui.py --snapshot data/processed/dynastyprocess_rankings_2026.json --scenario data/fixtures/rehearsal_user_pick_8.json
```

## Interactive CLI

Run the keyboard-driven terminal draft room with:

```bash
PYTHONPATH=. python scripts/draft_tui.py
```

Use arrow keys to move, Enter or `d` to draft, `/` to search, `u`/`r` for undo/redo, `s` to save, and `q` to quit. See [docs/cli.md](docs/cli.md) for the full shortcut list and custom snapshot usage.

## Local Setup

Backend checks:

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy bayesiandraft apps/api/src
```

The project targets Python 3.12. The current local machine also has an older system `python3`; use a modern interpreter explicitly if needed.

Frontend checks:

```bash
npm install
npm test
npm run lint
npm run build
```

Run the local API:

```bash
uvicorn bayesiandraft_api.main:app --app-dir apps/api/src --reload
```

Run the web app:

```bash
npm run dev
```

## Data And Privacy

BayesianDraft is designed to run locally. Committed examples use anonymized manager labels and synthetic fixture data. Do not commit real league credentials, cookies, ESPN tokens, private league data, local databases, or raw downloaded datasets.

## Development

- Keep league settings configuration-driven.
- Keep scoring and draft state deterministic and heavily tested.
- Prefer fixtures over live services in tests.
- Preserve data provenance and avoid historical leakage.
- Keep manual draft mode reliable before adding ESPN synchronization.
- Keep `main` runnable with focused commits and clear validation.

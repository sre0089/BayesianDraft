# BayesianDraft

BayesianDraft is a local-first probabilistic fantasy football draft assistant for configurable fantasy football leagues.

Most fantasy tools rank players. BayesianDraft ranks decisions. The target product recommends the available player who maximizes expected final roster strength, and eventually playoff and championship probability, given the live draft state.

## Target Stack

- Backend: Python 3.12, FastAPI, Pydantic, Polars, DuckDB or SQLite
- Frontend: React, TypeScript, Vite, Vitest, React Testing Library
- Testing: pytest, Ruff, mypy where practical, Vitest
- Modeling: scikit-learn first, CatBoost/LightGBM only when validated
- Storage: local configuration, data snapshots, draft sessions, model artifacts, and audit logs

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

## Development Principles

- Keep league settings configuration-driven.
- Keep scoring and draft state deterministic and heavily tested.
- Prefer fixtures over live services in tests.
- Preserve data provenance and avoid historical leakage.
- Keep manual draft mode reliable before adding ESPN synchronization.
- Build small, complete vertical slices and keep `main` runnable.

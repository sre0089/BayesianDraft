# BayesianDraft

BayesianDraft is a local-first probabilistic fantasy football draft assistant for a private 12-team ESPN full-PPR redraft league.

Most fantasy tools rank players. BayesianDraft ranks decisions. The target product recommends the available player who maximizes expected final roster strength, and eventually playoff and championship probability, given the live draft state.

## Source of Truth

The repository is governed by two master documents:

- `BayesianDraft_Project_Specification_FULL.md`
- `BayesianDraft_Engineering_Workflow_FULL.md`

Working docs in `docs/` summarize and operationalize those documents. If there is a conflict, the two master documents win until an ADR updates the decision.

## Target Stack

- Backend: Python 3.12, FastAPI, Pydantic, Polars, DuckDB or SQLite
- Frontend: React, TypeScript, Vite, Vitest, React Testing Library
- Testing: pytest, Ruff, mypy where practical, Vitest
- Modeling: scikit-learn first, CatBoost/LightGBM only when validated
- Storage: local configuration, data snapshots, draft sessions, model artifacts, and audit logs

## Current Status

Milestone 0 is in progress: repository foundation, documentation, tooling, and runnable skeletons.

No production recommendation logic exists yet.

## Development Principles

- Keep league settings configuration-driven.
- Keep scoring and draft state deterministic and heavily tested.
- Prefer fixtures over live services in tests.
- Preserve data provenance and avoid historical leakage.
- Keep manual draft mode reliable before adding ESPN synchronization.
- Build small, complete vertical slices and keep `main` runnable.

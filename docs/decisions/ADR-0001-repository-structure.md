# ADR-0001: Repository Structure

## Status

Accepted

## Context

BayesianDraft needs a local-first application, backend API, domain package, data artifacts, models, and documentation without mixing concerns.

## Decision

Use a monorepo with:

- `bayesiandraft/` for core Python domain logic.
- `apps/api/` for the FastAPI app.
- `apps/web/` for the React/Vite app.
- `configs/`, `data/`, `models/`, `scripts/`, `tests/`, and `docs/` for supporting project areas.

## Consequences

This keeps shared domain logic independent from the API and UI while allowing one CI pipeline and one repository for draft-day operation.

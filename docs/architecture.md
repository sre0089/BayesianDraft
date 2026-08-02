# Architecture

BayesianDraft should be a local-first monorepo with separated domain logic, API, frontend, data, modeling, simulation, and audit concerns.

## Target Components

- `bayesiandraft/`: core Python package for config, domain entities, scoring, draft state, rankings, recommendations, simulations, projections, data, and audit.
- `apps/api/`: FastAPI service exposing local backend workflows.
- `apps/web/`: React/TypeScript draft room, rankings, and simulator UI.
- `configs/`: versioned league configuration.
- `data/`: local fixtures, manifests, processed snapshots, and untracked raw data.
- `models/`: model artifacts, metadata, and registry files.
- `tests/`: unit, integration, simulation, and backtesting tests.

## Boundaries

- UI must not own scoring, draft progression, or recommendation rules.
- API must expose typed request/response models.
- Data ingestion must be separate from modeling.
- Recommendation orchestration must be separate from player projection models.
- Manual draft mode must work without ESPN synchronization.

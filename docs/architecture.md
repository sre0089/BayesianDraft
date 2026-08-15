# Architecture

BayesianDraft is organized as a local-first monorepo. The core draft logic lives in Python, with a small API and web app layered on top. The terminal UI uses the same engine code as the scripts and API, so behavior stays consistent across ways of running the project.

## Main Pieces

- `bayesiandraft/`: the core Python package. This is where draft state, scoring, rankings, recommendations, simulations, data loading, audits, and model helpers live.
- `apps/api/`: a FastAPI service for local draft-room workflows.
- `apps/web/`: a React/TypeScript draft room.
- `configs/`: public-safe league settings. Local overrides, such as real manager names, should use ignored `*.local.yaml` files.
- `data/`: synthetic fixtures plus ignored folders for raw downloads, processed snapshots, and draft saves.
- `docs/`: longer notes on methodology, data, simulation, UI, and maintenance.
- `bayesiandraft/modeling/`: local model registry helpers. Model artifacts and metadata should be created locally and kept out of git unless they are small, public, and intentionally versioned.
- `scripts/`: command-line tools for importing data, running the TUI, building path banks, exporting reports, and validating the repo.
- `tests/`: Python tests for the engine and scripts. API and web tests live next to those apps.

## Boundaries

- UI code should not own scoring, draft progression, or recommendation rules.
- API endpoints should stay thin and typed; the engine should do the real work.
- Data ingestion should stay separate from modeling and recommendations.
- Recommendation orchestration should stay separate from player projection models.
- Manual draft mode should work without ESPN synchronization.

## Why It Is Split This Way

Draft-day tools are stressful if they are hard to recover or debug. Keeping the engine deterministic and local makes it easier to test, inspect, and trust. The TUI, API, and web app are different front ends over the same draft state and recommendation code.

The project can still grow into richer projection models or ESPN sync, but those pieces should improve the local workflow instead of replacing it.

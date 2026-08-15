# Contributing

Thanks for checking out BayesianDraft. This is a small local-first project, so the best contributions are usually focused: a clearer command, a tighter test, a better explanation, or one draft-room improvement that is easy to review.

## Before You Change Code

- Skim the README and the doc page closest to the thing you want to touch.
- Check whether there is already a script or helper for the workflow.
- Keep real league data local. Public examples should use anonymized managers and synthetic fixtures.

## How To Work

- Make one meaningful change at a time.
- Prefer boring, readable code over clever abstractions.
- Keep scoring, draft state, and simulations deterministic when possible.
- Use fixtures in tests instead of live services.
- Add tests when behavior changes, especially around draft state, recommendations, simulation, or data loading.

## Local Checks

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

For a broader local sweep:

```bash
PYTHONPATH=.:apps/api/src python scripts/ci_local.py
```

## Public Safety

Please do not commit:

- real manager names
- private league exports
- ESPN cookies or tokens
- API keys
- local draft saves
- raw downloaded datasets
- `node_modules`, virtual environments, caches, or build output

If you want the TUI to show your real league names, use a local ignored config such as:

```text
configs/leagues/espn_2026.local.yaml
```

## Pull Requests

A good PR includes:

- what changed
- how you tested it
- any limitations or follow-up work

Small PRs are much easier to review than large cleanups mixed with feature work.

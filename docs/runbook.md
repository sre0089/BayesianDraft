# Draft-Day Runbook

Milestone 27 adds the local operational runbook.

## Before Draft

Run:

```bash
PYTHONPATH=.:apps/api/src python scripts/validate_local.py
pytest -q
ruff check .
mypy bayesiandraft apps/api/src scripts/export_baseline_rankings.py scripts/verify_ingestion_manifest.py scripts/preflight.py scripts/data_refresh.py scripts/export_openapi.py scripts/version_info.py scripts/rehearsal_preview.py scripts/validate_local.py
```

For the web app:

```bash
cd apps/web
npm test
npm run lint
npm run build
```

For a compact handoff snapshot:

```bash
PYTHONPATH=. python scripts/project_status.py
```

## During Draft

- Prefer manual draft tracking if ESPN credentials or sync behavior is uncertain.
- Save draft state after major pick clusters.
- Use rehearsal scenarios to practice the user-on-clock workflow.
- Keep real manager names out of committed files.

## After Draft

- Persist decision audit events.
- Export final draft state.
- Record model versions, data snapshots, and notes for post-season review.

# API

The local API should be implemented with FastAPI.

Initial endpoint groups:

- Health
- League config
- Draft creation and state
- Available players
- Record pick
- Undo and redo
- Edit pick
- Manager rosters
- User roster
- Rankings
- Position-based recommendation groups
- Player details
- Save and load draft

Request and response models must be typed, validation errors should be useful, and integration tests should cover the full manual draft workflow.

## Implemented Local Endpoints

- `GET /health`
- `GET /version`
- `GET /league`
- `GET /players`
- `GET /rankings`
- `POST /drafts`
- `GET /drafts/{draft_id}`
- `GET /drafts/{draft_id}/available-players`
- `POST /drafts/{draft_id}/picks`
- `POST /drafts/{draft_id}/undo`
- `POST /drafts/{draft_id}/redo`
- `PATCH /drafts/{draft_id}/picks`
- `GET /drafts/{draft_id}/rosters`
- `GET /drafts/{draft_id}/rosters/user`
- `GET /drafts/{draft_id}/recommendations`
- `GET /drafts/{draft_id}/recommendations/by-position`
- `GET /drafts/{draft_id}/candidate-rollouts`
- `POST /drafts/{draft_id}/save`
- `POST /drafts/load`

The current service stores draft sessions in memory and defaults to the synthetic baseline player snapshot. Save/load can persist a draft JSON file locally.
Candidate rollouts require the user manager to be on clock. `GET /drafts/{draft_id}/candidate-rollouts` accepts `limit`, `simulation_count`, and `per_needed_position` query parameters. The position parameter seeds the rollout candidate pool with top players from positions the configured user roster still needs before filling the rest by overall rank.

Use `BAYESIANDRAFT_PLAYER_SNAPSHOT_PATH` to run the local API with an imported snapshot:

```bash
BAYESIANDRAFT_PLAYER_SNAPSHOT_PATH=data/processed/my_snapshot.json \
  uvicorn bayesiandraft_api.main:app --app-dir apps/api/src --reload
```

ESPN sync is currently represented by a dry-run integration boundary in `bayesiandraft.integrations.espn`; no live ESPN endpoint is exposed yet.

## Contract Export

OpenAPI schema export is available:

```bash
PYTHONPATH=.:apps/api/src python scripts/export_openapi.py --out /tmp/bayesiandraft-openapi.json
```

API contract tests assert that key draft, recommendation, and rollout endpoints remain present.

## Current Limitations

- No authentication is implemented, matching local-first development.
- In-memory draft sessions reset when the API process restarts unless saved and loaded.
- API responses are intentionally broad JSON payloads while frontend and domain contracts stabilize.

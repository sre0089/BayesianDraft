from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bayesiandraft.draft import DraftState, DraftStateError
from bayesiandraft.recommendations import (
    CandidateOptimizerConfig,
    optimize_candidates,
    recommend_players,
)
from bayesiandraft.release import BuildInfo, build_info_from_env
from bayesiandraft_api.service import DraftSessionService, to_api_draft_state


class HealthResponse(BaseModel):
    status: str


class CreateDraftRequest(BaseModel):
    draft_id: str | None = None


class RecordPickRequest(BaseModel):
    player_id: str
    manager_id: str | None = None


class EditPickRequest(BaseModel):
    overall_pick: int
    player_id: str


class SaveDraftRequest(BaseModel):
    path: str


class LoadDraftRequest(BaseModel):
    path: str


def create_app() -> FastAPI:
    app = FastAPI(title="BayesianDraft API")
    service = DraftSessionService()

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/version", response_model=BuildInfo)
    def version() -> BuildInfo:
        return build_info_from_env()

    @app.get("/league")
    def league() -> dict[str, object]:
        return service.league_config.model_dump(mode="json")

    @app.get("/players")
    def players() -> list[dict[str, object]]:
        return [player.model_dump(mode="json") for player in service.player_snapshot.players]

    @app.get("/rankings")
    def rankings() -> list[dict[str, object]]:
        return [ranking.model_dump(mode="json") for ranking in service.rankings()]

    @app.post("/drafts")
    def create_draft(request: CreateDraftRequest) -> dict[str, object]:
        state = service.create_draft(draft_id=request.draft_id)
        return to_api_draft_state(state).model_dump(mode="json")

    @app.get("/drafts/{draft_id}")
    def get_draft(draft_id: str) -> dict[str, object]:
        return _state_response(service, draft_id)

    @app.get("/drafts/{draft_id}/available-players")
    def available_players(draft_id: str) -> list[dict[str, object]]:
        state = _get_state_or_404(service, draft_id)
        return [
            state.players[player_id].model_dump(mode="json")
            for player_id in state.available_player_ids
        ]

    @app.post("/drafts/{draft_id}/picks")
    def record_pick(draft_id: str, request: RecordPickRequest) -> dict[str, object]:
        state = _get_state_or_404(service, draft_id)
        try:
            return _replace_and_respond(
                service,
                state.record_pick(request.player_id, manager_id=request.manager_id),
            )
        except DraftStateError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/drafts/{draft_id}/undo")
    def undo(draft_id: str) -> dict[str, object]:
        state = _get_state_or_404(service, draft_id)
        try:
            return _replace_and_respond(service, state.undo())
        except DraftStateError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/drafts/{draft_id}/redo")
    def redo(draft_id: str) -> dict[str, object]:
        state = _get_state_or_404(service, draft_id)
        try:
            return _replace_and_respond(service, state.redo())
        except DraftStateError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.patch("/drafts/{draft_id}/picks")
    def edit_pick(draft_id: str, request: EditPickRequest) -> dict[str, object]:
        state = _get_state_or_404(service, draft_id)
        try:
            return _replace_and_respond(
                service,
                state.edit_pick(request.overall_pick, request.player_id),
            )
        except DraftStateError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/drafts/{draft_id}/rosters")
    def rosters(draft_id: str) -> dict[str, dict[str, object]]:
        state = _get_state_or_404(service, draft_id)
        return {
            manager_id: roster.model_dump(mode="json")
            for manager_id, roster in state.rosters.items()
        }

    @app.get("/drafts/{draft_id}/rosters/user")
    def user_roster(draft_id: str) -> dict[str, object]:
        state = _get_state_or_404(service, draft_id)
        user_manager_id = state.league_config.league.user_manager_id
        return state.rosters[user_manager_id].model_dump(mode="json")

    @app.get("/drafts/{draft_id}/recommendations")
    def recommendations(draft_id: str) -> dict[str, object]:
        state = _get_state_or_404(service, draft_id)
        try:
            result = recommend_players(state, service.rankings())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return result.model_dump(mode="json")

    @app.get("/drafts/{draft_id}/candidate-rollouts")
    def candidate_rollouts(
        draft_id: str,
        limit: int = 4,
        simulation_count: int = 25,
    ) -> dict[str, object]:
        state = _get_state_or_404(service, draft_id)
        try:
            result = optimize_candidates(
                state,
                service.rankings(),
                config=CandidateOptimizerConfig(
                    limit=limit,
                    candidate_pool_size=max(limit * 2, limit),
                    simulation_count=simulation_count,
                ),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return result.model_dump(mode="json")

    @app.post("/drafts/{draft_id}/save")
    def save_draft(draft_id: str, request: SaveDraftRequest) -> dict[str, str]:
        state = _get_state_or_404(service, draft_id)
        try:
            state.save(request.path)
        except OSError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"status": "saved", "path": request.path}

    @app.post("/drafts/load")
    def load_draft(request: LoadDraftRequest) -> dict[str, object]:
        try:
            state = DraftState.load(Path(request.path))
        except DraftStateError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _replace_and_respond(service, state)

    return app


def _get_state_or_404(service: DraftSessionService, draft_id: str) -> DraftState:
    try:
        return service.get_draft(draft_id)
    except DraftStateError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _state_response(service: DraftSessionService, draft_id: str) -> dict[str, object]:
    return to_api_draft_state(_get_state_or_404(service, draft_id)).model_dump(mode="json")


def _replace_and_respond(service: DraftSessionService, state: DraftState) -> dict[str, object]:
    return to_api_draft_state(service.replace_draft(state)).model_dump(mode="json")


app = create_app()

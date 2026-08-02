from pathlib import Path

from pydantic import BaseModel

from bayesiandraft.config import LeagueConfig, load_league_config
from bayesiandraft.data import PlayerSnapshot, load_player_snapshot
from bayesiandraft.draft import DraftState, DraftStateError, Player
from bayesiandraft.rankings import RankingRow, build_baseline_rankings

DEFAULT_LEAGUE_CONFIG_PATH = Path("configs/leagues/espn_2026.yaml")
DEFAULT_PLAYER_SNAPSHOT_PATH = Path("data/fixtures/baseline_players_2026.json")


class ApiDraftState(BaseModel):
    draft_id: str
    current_overall_pick: int
    current_round: int | None
    current_round_pick: int | None
    manager_on_clock: str | None
    total_rounds: int
    total_picks: int
    is_complete: bool
    completed_picks: list[dict[str, object]]
    available_player_ids: list[str]
    rosters: dict[str, dict[str, object]]
    user_future_picks: list[dict[str, object]]


class DraftSessionService:
    def __init__(
        self,
        *,
        league_config_path: Path = DEFAULT_LEAGUE_CONFIG_PATH,
        player_snapshot_path: Path = DEFAULT_PLAYER_SNAPSHOT_PATH,
    ) -> None:
        self.league_config_path = league_config_path
        self.player_snapshot_path = player_snapshot_path
        self._drafts: dict[str, DraftState] = {}

    @property
    def league_config(self) -> LeagueConfig:
        return load_league_config(self.league_config_path)

    @property
    def player_snapshot(self) -> PlayerSnapshot:
        return load_player_snapshot(self.player_snapshot_path)

    def rankings(self) -> list[RankingRow]:
        return build_baseline_rankings(self.player_snapshot)

    def create_draft(self, *, draft_id: str | None = None) -> DraftState:
        snapshot = self.player_snapshot
        players = [
            Player(
                player_id=player.player_id,
                full_name=player.full_name,
                position=player.position.value,
                nfl_team_id=player.nfl_team_id,
            )
            for player in snapshot.players
        ]
        state = DraftState.create(self.league_config, players, draft_id=draft_id)
        self._drafts[state.draft_id] = state
        return state

    def get_draft(self, draft_id: str) -> DraftState:
        try:
            return self._drafts[draft_id]
        except KeyError as exc:
            raise DraftStateError("unknown draft_id") from exc

    def replace_draft(self, state: DraftState) -> DraftState:
        self._drafts[state.draft_id] = state
        return state


def to_api_draft_state(state: DraftState) -> ApiDraftState:
    return ApiDraftState(
        draft_id=state.draft_id,
        current_overall_pick=state.current_overall_pick,
        current_round=state.current_round,
        current_round_pick=state.current_round_pick,
        manager_on_clock=state.manager_on_clock,
        total_rounds=state.total_rounds,
        total_picks=state.total_picks,
        is_complete=state.is_complete,
        completed_picks=[pick.model_dump(mode="json") for pick in state.completed_picks],
        available_player_ids=state.available_player_ids,
        rosters={
            manager_id: roster.model_dump(mode="json")
            for manager_id, roster in state.rosters.items()
        },
        user_future_picks=[slot.model_dump(mode="json") for slot in state.user_future_picks],
    )

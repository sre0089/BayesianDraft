from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, ValidationError

from bayesiandraft.config import LeagueConfig


class DraftStateError(ValueError):
    """Raised when a draft state transition is invalid."""


class Player(BaseModel):
    player_id: str
    full_name: str
    position: str
    nfl_team_id: str | None = None


class DraftPick(BaseModel):
    overall_pick: PositiveInt
    round: PositiveInt
    round_pick: PositiveInt
    manager_id: str
    player_id: str
    source: str = "manual"
    manually_entered: bool = True
    corrected: bool = False
    prior_pick_reference: int | None = None


class Roster(BaseModel):
    manager_id: str
    player_ids: list[str] = Field(default_factory=list)
    positional_counts: dict[str, int] = Field(default_factory=dict)


class PickSlot(BaseModel):
    overall_pick: PositiveInt
    round: PositiveInt
    round_pick: PositiveInt
    manager_id: str


class DraftState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=False)

    draft_id: str
    league_config: LeagueConfig
    players: dict[str, Player]
    total_rounds: PositiveInt
    completed_picks: list[DraftPick] = Field(default_factory=list)
    rosters: dict[str, Roster] = Field(default_factory=dict)
    undo_stack: list[list[DraftPick]] = Field(default_factory=list)
    redo_stack: list[list[DraftPick]] = Field(default_factory=list)

    @property
    def total_picks(self) -> int:
        return self.league_config.league.team_count * self.total_rounds

    @property
    def current_overall_pick(self) -> int:
        return len(self.completed_picks) + 1

    @property
    def is_complete(self) -> bool:
        return len(self.completed_picks) >= self.total_picks

    @property
    def current_pick_slot(self) -> PickSlot | None:
        if self.is_complete:
            return None
        return pick_slot_for_overall_pick(self.current_overall_pick, self.league_config)

    @property
    def current_round(self) -> int | None:
        slot = self.current_pick_slot
        return None if slot is None else slot.round

    @property
    def current_round_pick(self) -> int | None:
        slot = self.current_pick_slot
        return None if slot is None else slot.round_pick

    @property
    def manager_on_clock(self) -> str | None:
        slot = self.current_pick_slot
        return None if slot is None else slot.manager_id

    @property
    def available_player_ids(self) -> list[str]:
        drafted_player_ids = {pick.player_id for pick in self.completed_picks}
        return [player_id for player_id in self.players if player_id not in drafted_player_ids]

    @property
    def user_future_picks(self) -> list[PickSlot]:
        current_pick = self.current_overall_pick
        return [
            pick_slot_for_overall_pick(overall_pick, self.league_config)
            for overall_pick in range(current_pick, self.total_picks + 1)
            if pick_slot_for_overall_pick(overall_pick, self.league_config).manager_id
            == self.league_config.league.user_manager_id
        ]

    @classmethod
    def create(
        cls,
        league_config: LeagueConfig,
        players: list[Player],
        *,
        draft_id: str | None = None,
        total_rounds: int | None = None,
    ) -> "DraftState":
        rounds = total_rounds or default_total_rounds(league_config)
        player_map = {player.player_id: player for player in players}
        if len(player_map) != len(players):
            raise DraftStateError("players must have unique player_id values")

        rosters = {
            manager.id: Roster(manager_id=manager.id) for manager in league_config.draft_order
        }
        return cls(
            draft_id=draft_id or str(uuid4()),
            league_config=league_config,
            players=player_map,
            total_rounds=rounds,
            rosters=rosters,
        )

    def record_pick(self, player_id: str, manager_id: str | None = None) -> "DraftState":
        slot = self.current_pick_slot
        if slot is None:
            raise DraftStateError("draft is already complete")

        selected_manager_id = manager_id or slot.manager_id
        if selected_manager_id != slot.manager_id:
            raise DraftStateError("manager_id must match manager on clock")
        self._validate_available_player(player_id)

        pick = DraftPick(
            overall_pick=slot.overall_pick,
            round=slot.round,
            round_pick=slot.round_pick,
            manager_id=selected_manager_id,
            player_id=player_id,
        )
        completed_picks = [*self.completed_picks, pick]
        return self._with_completed_picks(
            completed_picks,
            undo_stack=[*self.undo_stack, self.completed_picks],
            redo_stack=[],
        )

    def undo(self) -> "DraftState":
        if not self.undo_stack:
            raise DraftStateError("nothing to undo")

        previous_completed_picks = self.undo_stack[-1]
        return self._with_completed_picks(
            previous_completed_picks,
            undo_stack=self.undo_stack[:-1],
            redo_stack=[self.completed_picks, *self.redo_stack],
        )

    def redo(self) -> "DraftState":
        if not self.redo_stack:
            raise DraftStateError("nothing to redo")

        next_completed_picks = self.redo_stack[0]
        return self._with_completed_picks(
            next_completed_picks,
            undo_stack=[*self.undo_stack, self.completed_picks],
            redo_stack=self.redo_stack[1:],
        )

    def edit_pick(self, overall_pick: int, player_id: str) -> "DraftState":
        if overall_pick < 1 or overall_pick > len(self.completed_picks):
            raise DraftStateError("overall_pick must reference a completed pick")

        existing_pick = self.completed_picks[overall_pick - 1]
        drafted_elsewhere = {
            pick.player_id
            for pick in self.completed_picks
            if pick.overall_pick != existing_pick.overall_pick
        }
        if player_id in drafted_elsewhere:
            raise DraftStateError("player has already been drafted")
        if player_id not in self.players:
            raise DraftStateError("unknown player_id")

        edited_pick = existing_pick.model_copy(
            update={
                "player_id": player_id,
                "corrected": True,
                "prior_pick_reference": existing_pick.overall_pick,
            }
        )
        completed_picks = [
            edited_pick if pick.overall_pick == overall_pick else pick
            for pick in self.completed_picks
        ]
        return self._with_completed_picks(
            completed_picks,
            undo_stack=[*self.undo_stack, self.completed_picks],
            redo_stack=[],
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "DraftState":
        try:
            return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValidationError) as exc:
            raise DraftStateError(f"Unable to load draft state: {path}") from exc

    def _with_completed_picks(
        self,
        completed_picks: list[DraftPick],
        *,
        undo_stack: list[list[DraftPick]],
        redo_stack: list[list[DraftPick]],
    ) -> "DraftState":
        return self.model_copy(
            update={
                "completed_picks": completed_picks,
                "rosters": build_rosters(self.league_config, completed_picks, self.players),
                "undo_stack": undo_stack,
                "redo_stack": redo_stack,
            }
        )

    def _validate_available_player(self, player_id: str) -> None:
        if player_id not in self.players:
            raise DraftStateError("unknown player_id")
        if player_id not in self.available_player_ids:
            raise DraftStateError("player has already been drafted")


def default_total_rounds(league_config: LeagueConfig) -> int:
    return sum(league_config.roster.starting_slots.values()) + league_config.roster.bench_slots


def pick_slot_for_overall_pick(overall_pick: int, league_config: LeagueConfig) -> PickSlot:
    if overall_pick < 1:
        raise DraftStateError("overall_pick must be positive")

    team_count = league_config.league.team_count
    draft_index = overall_pick - 1
    round_number = draft_index // team_count + 1
    index_in_round = draft_index % team_count
    round_pick = index_in_round + 1

    if round_number % 2 == 1:
        manager_index = index_in_round
    else:
        manager_index = team_count - index_in_round - 1

    return PickSlot(
        overall_pick=overall_pick,
        round=round_number,
        round_pick=round_pick,
        manager_id=league_config.draft_order[manager_index].id,
    )


def build_rosters(
    league_config: LeagueConfig,
    completed_picks: list[DraftPick],
    players: dict[str, Player] | None = None,
) -> dict[str, Roster]:
    rosters = {manager.id: Roster(manager_id=manager.id) for manager in league_config.draft_order}
    for pick in completed_picks:
        if pick.manager_id not in rosters:
            raise DraftStateError("pick references unknown manager_id")
        rosters[pick.manager_id].player_ids.append(pick.player_id)
        if players is not None:
            if pick.player_id not in players:
                raise DraftStateError("pick references unknown player_id")
            position = players[pick.player_id].position
            current_count = rosters[pick.manager_id].positional_counts.get(position, 0)
            rosters[pick.manager_id].positional_counts[position] = current_count + 1
    return rosters

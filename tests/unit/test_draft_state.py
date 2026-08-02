from collections.abc import Iterator
from pathlib import Path

import pytest

from bayesiandraft.config import LeagueConfig, load_league_config
from bayesiandraft.draft import (
    DraftPick,
    DraftState,
    DraftStateError,
    Player,
    default_total_rounds,
    pick_slot_for_overall_pick,
)


@pytest.fixture(scope="module")
def league_config() -> Iterator[LeagueConfig]:
    yield load_league_config(Path("configs/leagues/espn_2026.yaml"))


@pytest.fixture()
def players() -> list[Player]:
    return [
        Player(player_id=f"player_{index:03}", full_name=f"Player {index:03}", position="WR")
        for index in range(1, 220)
    ]


def test_default_total_rounds_excludes_ir(league_config: LeagueConfig) -> None:
    assert default_total_rounds(league_config) == 16


def test_round_one_draft_order(league_config: LeagueConfig) -> None:
    manager_ids = [
        pick_slot_for_overall_pick(overall_pick, league_config).manager_id
        for overall_pick in range(1, 13)
    ]

    assert manager_ids == [manager.id for manager in league_config.draft_order]


def test_round_two_reverses_draft_order(league_config: LeagueConfig) -> None:
    manager_ids = [
        pick_slot_for_overall_pick(overall_pick, league_config).manager_id
        for overall_pick in range(13, 25)
    ]

    assert manager_ids == [manager.id for manager in reversed(league_config.draft_order)]


@pytest.mark.parametrize(
    ("overall_pick", "round_number", "round_pick"),
    [
        (9, 1, 9),
        (16, 2, 4),
        (33, 3, 9),
        (40, 4, 4),
    ],
)
def test_user_snake_pick_positions(
    league_config: LeagueConfig,
    overall_pick: int,
    round_number: int,
    round_pick: int,
) -> None:
    slot = pick_slot_for_overall_pick(overall_pick, league_config)

    assert slot.manager_id == league_config.league.user_manager_id
    assert slot.round == round_number
    assert slot.round_pick == round_pick


def test_new_draft_state_tracks_current_pick_and_future_user_picks(
    league_config: LeagueConfig,
    players: list[Player],
) -> None:
    state = DraftState.create(league_config, players, draft_id="draft_test")

    assert state.current_overall_pick == 1
    assert state.current_round == 1
    assert state.current_round_pick == 1
    assert state.manager_on_clock == "manager_01"
    assert [slot.overall_pick for slot in state.user_future_picks[:4]] == [9, 16, 33, 40]


def test_record_pick_advances_state_and_roster(
    league_config: LeagueConfig,
    players: list[Player],
) -> None:
    state = DraftState.create(league_config, players)

    next_state = state.record_pick("player_001")

    assert next_state.current_overall_pick == 2
    assert "player_001" not in next_state.available_player_ids
    assert next_state.rosters["manager_01"].player_ids == ["player_001"]
    assert next_state.rosters["manager_01"].positional_counts == {"WR": 1}
    assert state.current_overall_pick == 1


def test_rejects_duplicate_player(
    league_config: LeagueConfig,
    players: list[Player],
) -> None:
    state = DraftState.create(league_config, players).record_pick("player_001")

    with pytest.raises(DraftStateError, match="already been drafted"):
        state.record_pick("player_001")


def test_rejects_invalid_manager_for_pick(
    league_config: LeagueConfig,
    players: list[Player],
) -> None:
    state = DraftState.create(league_config, players)

    with pytest.raises(DraftStateError, match="manager on clock"):
        state.record_pick("player_001", manager_id="manager_02")


def test_undo_and_redo_restore_state(
    league_config: LeagueConfig,
    players: list[Player],
) -> None:
    state = DraftState.create(league_config, players)
    state = state.record_pick("player_001")
    state = state.record_pick("player_002")

    undone = state.undo()
    redone = undone.redo()

    assert undone.current_overall_pick == 2
    assert undone.rosters["manager_02"].player_ids == []
    assert "player_002" in undone.available_player_ids
    assert redone.completed_picks == state.completed_picks
    assert redone.rosters == state.rosters


def test_edit_prior_pick_updates_rosters_and_clears_redo(
    league_config: LeagueConfig,
    players: list[Player],
) -> None:
    state = DraftState.create(league_config, players)
    state = state.record_pick("player_001")
    state = state.record_pick("player_002")

    edited = state.edit_pick(overall_pick=1, player_id="player_003")

    assert edited.completed_picks[0].player_id == "player_003"
    assert edited.completed_picks[0].corrected is True
    assert edited.rosters["manager_01"].player_ids == ["player_003"]
    assert edited.rosters["manager_01"].positional_counts == {"WR": 1}
    assert "player_001" in edited.available_player_ids
    assert edited.redo_stack == []


def test_save_and_load_round_trip(
    tmp_path: Path,
    league_config: LeagueConfig,
    players: list[Player],
) -> None:
    state = DraftState.create(league_config, players, draft_id="draft_test")
    state = state.record_pick("player_001")
    state = state.record_pick("player_002")
    save_path = tmp_path / "draft_state.json"

    state.save(save_path)
    loaded_state = DraftState.load(save_path)

    assert loaded_state == state


def test_builds_state_from_completed_picks(
    league_config: LeagueConfig,
    players: list[Player],
) -> None:
    state = DraftState.create(league_config, players, draft_id="draft_test")
    pick = DraftPick(
        overall_pick=1,
        round=1,
        round_pick=1,
        manager_id="manager_01",
        player_id="player_001",
    )
    rebuilt = state.model_copy(
        update={
            "completed_picks": [pick],
            "rosters": {"manager_01": state.rosters["manager_01"]},
        }
    )

    assert rebuilt.completed_picks[0].manager_id == "manager_01"


def test_complete_mock_draft_can_be_entered(
    league_config: LeagueConfig,
    players: list[Player],
) -> None:
    state = DraftState.create(league_config, players)

    for index in range(state.total_picks):
        state = state.record_pick(players[index].player_id)

    assert state.is_complete is True
    assert state.current_pick_slot is None
    assert state.manager_on_clock is None
    assert len(state.completed_picks) == 192
    assert state.available_player_ids == [player.player_id for player in players[192:]]

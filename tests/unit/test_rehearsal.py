from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import (
    DraftState,
    Player,
    apply_rehearsal_scenario,
    load_rehearsal_scenario,
)


def _draft_state() -> DraftState:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    players = [
        Player(
            player_id=player.player_id,
            full_name=player.full_name,
            position=player.position.value,
            nfl_team_id=player.nfl_team_id,
        )
        for player in snapshot.players
    ]
    return DraftState.create(load_league_config("configs/leagues/espn_2026.yaml"), players)


def test_rehearsal_scenario_moves_to_user_pick() -> None:
    scenario = load_rehearsal_scenario("data/fixtures/rehearsal_user_pick_8.json")

    rehearsed = apply_rehearsal_scenario(_draft_state(), scenario)

    assert rehearsed.current_overall_pick == 8
    assert rehearsed.manager_on_clock == "user_manager"


def test_rehearsal_scenario_records_unique_picks() -> None:
    scenario = load_rehearsal_scenario("data/fixtures/rehearsal_user_pick_8.json")
    rehearsed = apply_rehearsal_scenario(_draft_state(), scenario)

    player_ids = [pick.player_id for pick in rehearsed.completed_picks]

    assert len(player_ids) == len(set(player_ids))

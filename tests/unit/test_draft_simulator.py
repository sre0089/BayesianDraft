from pathlib import Path

import pytest

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import DraftState, Player
from bayesiandraft.rankings import RankingRow, build_baseline_rankings
from bayesiandraft.simulation import (
    DraftSimulationConfig,
    simulate_candidate_rollout,
    simulate_remaining_draft,
)


def _state_and_rankings() -> tuple[DraftState, list[RankingRow]]:
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
    state = DraftState.create(load_league_config("configs/leagues/espn_2026.yaml"), players)
    return state, build_baseline_rankings(snapshot)


def _state_with_user_on_clock() -> DraftState:
    state, _rankings = _state_and_rankings()
    for player_id in ["rb_001", "wr_001", "rb_002", "wr_002", "qb_001", "te_001", "wr_003"]:
        state = state.record_pick(player_id)
    return state


def test_remaining_draft_is_reproducible_for_seed() -> None:
    state, rankings = _state_and_rankings()

    first = simulate_remaining_draft(state, rankings, seed=9)
    second = simulate_remaining_draft(state, rankings, seed=9)

    assert first == second
    assert first.stopped_reason == "no_ranked_players_available"


def test_remaining_draft_does_not_duplicate_players() -> None:
    state, rankings = _state_and_rankings()

    simulated = simulate_remaining_draft(state, rankings, seed=12)
    drafted_player_ids = [pick.player_id for pick in simulated.completed_picks]

    assert len(drafted_player_ids) == len(set(drafted_player_ids))
    assert not simulated.remaining_player_ids


def test_candidate_rollout_adds_candidate_to_user_roster() -> None:
    _state, rankings = _state_and_rankings()
    state = _state_with_user_on_clock()

    result = simulate_candidate_rollout(
        state,
        rankings,
        candidate_player_id="rb_003",
        config=DraftSimulationConfig(simulation_count=8, seed=21),
    )

    assert result.candidate_player_id == "rb_003"
    assert result.average_roster_size >= 1
    assert result.average_projected_points > 0
    assert result.roster_position_counts["RB"] >= 1


def test_candidate_rollout_requires_user_on_clock() -> None:
    state, rankings = _state_and_rankings()

    with pytest.raises(ValueError, match="user manager"):
        simulate_candidate_rollout(state, rankings, candidate_player_id="rb_001")

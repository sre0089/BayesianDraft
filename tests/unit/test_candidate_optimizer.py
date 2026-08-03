from pathlib import Path

import pytest

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import DraftState, Player
from bayesiandraft.rankings import RankingRow, build_baseline_rankings
from bayesiandraft.recommendations import CandidateOptimizerConfig, optimize_candidates


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
    for player_id in ["rb_001", "wr_001", "qb_001", "rb_002", "wr_002", "te_001", "wr_003"]:
        state = state.record_pick(player_id)
    return state


def test_candidate_optimizer_is_seeded() -> None:
    _state, rankings = _state_and_rankings()
    state = _state_with_user_on_clock()
    config = CandidateOptimizerConfig(candidate_pool_size=3, simulation_count=6, seed=10)

    first = optimize_candidates(state, rankings, config=config)
    second = optimize_candidates(state, rankings, config=config)

    assert first == second
    assert first.primary.player_id in state.available_player_ids
    assert first.primary.explanation


def test_candidate_optimizer_returns_alternatives() -> None:
    _state, rankings = _state_and_rankings()
    result = optimize_candidates(
        _state_with_user_on_clock(),
        rankings,
        config=CandidateOptimizerConfig(limit=3, candidate_pool_size=4, simulation_count=4),
    )

    assert len(result.alternatives) == 2
    assert result.simulation_count == 4


def test_candidate_optimizer_requires_user_on_clock() -> None:
    state, rankings = _state_and_rankings()

    with pytest.raises(ValueError, match="user manager"):
        optimize_candidates(state, rankings)

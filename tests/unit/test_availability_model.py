from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import DraftState, Player
from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import (
    AvailabilityConfig,
    estimate_all_availability,
    estimate_availability,
)


def _state_and_rankings() -> tuple[DraftState, list]:
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


def test_availability_is_reproducible_for_seed() -> None:
    state, rankings = _state_and_rankings()
    config = AvailabilityConfig(simulation_count=100)

    first = estimate_availability(state, rankings, player_id="rb_001", seed=42, config=config)
    second = estimate_availability(state, rankings, player_id="rb_001", seed=42, config=config)

    assert first == second
    assert first.target_pick == 8
    assert 0 <= first.probability <= 1


def test_drafted_player_availability_is_zero() -> None:
    state, rankings = _state_and_rankings()
    state = state.record_pick("rb_001")

    estimate = estimate_availability(
        state,
        rankings,
        player_id="rb_001",
        seed=1,
        config=AvailabilityConfig(simulation_count=20),
    )

    assert estimate.probability == 0


def test_estimates_all_available_players() -> None:
    state, rankings = _state_and_rankings()

    estimates = estimate_all_availability(
        state,
        rankings,
        seed=7,
        config=AvailabilityConfig(simulation_count=20),
    )

    assert {estimate.player_id for estimate in estimates} == set(state.available_player_ids)

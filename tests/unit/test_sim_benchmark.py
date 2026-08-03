from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import DraftState, Player
from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import benchmark_remaining_draft


def test_simulation_benchmark_reports_elapsed_time() -> None:
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

    result = benchmark_remaining_draft(state, build_baseline_rankings(snapshot), seed=2)

    assert result.seed == 2
    assert result.completed_pick_count == 12
    assert result.elapsed_seconds >= 0

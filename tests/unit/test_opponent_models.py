from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import DraftState, Player
from bayesiandraft.opponents import build_opponent_profiles, opponent_pick_weight
from bayesiandraft.rankings import RankingRow, build_baseline_rankings
from bayesiandraft.simulation import simulate_remaining_draft


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


def test_builds_smoothed_opponent_profiles() -> None:
    state, rankings = _state_and_rankings()
    state = state.record_pick("rb_001")

    profiles = build_opponent_profiles(state, rankings)

    assert profiles["manager_01"].picks_observed == 1
    assert profiles["manager_01"].position_counts["RB"] == 1
    assert profiles["manager_02"].picks_observed == 0
    assert profiles["manager_02"].position_preferences


def test_opponent_pick_weight_uses_manager_preferences() -> None:
    state, rankings = _state_and_rankings()
    state = state.record_pick("rb_001")
    profiles = build_opponent_profiles(state, rankings)
    rb_ranking = next(ranking for ranking in rankings if ranking.player_id == "rb_002")
    qb_ranking = next(ranking for ranking in rankings if ranking.player_id == "qb_002")

    rb_weight = opponent_pick_weight("manager_01", rb_ranking, profiles)
    qb_weight = opponent_pick_weight("manager_01", qb_ranking, profiles)

    assert rb_weight > qb_weight


def test_draft_simulator_remains_seeded_with_opponent_profiles() -> None:
    state, rankings = _state_and_rankings()
    state = state.record_pick("rb_001")

    first = simulate_remaining_draft(state, rankings, seed=4)
    second = simulate_remaining_draft(state, rankings, seed=4)

    assert first == second

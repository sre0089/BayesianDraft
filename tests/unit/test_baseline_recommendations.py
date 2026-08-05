from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import DraftState, Player
from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.recommendations import recommend_players, recommend_players_by_needed_position


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


def test_recommendation_returns_primary_and_alternatives() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    result = recommend_players(_draft_state(), build_baseline_rankings(snapshot))

    assert result.primary.player_id == "rb_001"
    assert result.primary.confidence > 0
    assert result.primary.explanation
    assert len(result.alternatives) == 3


def test_recommendation_changes_after_player_is_drafted() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    state = _draft_state().record_pick("rb_001")
    result = recommend_players(state, build_baseline_rankings(snapshot))

    assert result.primary.player_id != "rb_001"


def test_recommendation_penalizes_early_kicker() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    state = _draft_state()
    result = recommend_players(state, build_baseline_rankings(snapshot), limit=12)
    kicker = next(
        score for score in [result.primary, *result.alternatives] if score.player_id == "k_001"
    )

    assert kicker.penalty == 45
    assert any("K/DST" in item for item in kicker.explanation)


def test_groups_recommendations_by_needed_position() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    groups = recommend_players_by_needed_position(_draft_state(), build_baseline_rankings(snapshot))

    assert {group.position for group in groups} >= {"QB", "RB", "WR", "TE", "DST", "K"}
    rb_group = next(group for group in groups if group.position == "RB")
    assert rb_group.remaining_need == 2
    assert rb_group.candidates[0].player_id == "rb_001"
    assert len(rb_group.candidates) <= 5


def test_position_groups_drop_filled_positions() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    state = _draft_state()
    for player_id in ["rb_001", "wr_001", "rb_002", "wr_002", "te_001", "wr_003", "rb_003"]:
        state = state.record_pick(player_id)
    state = state.record_pick("qb_001")
    groups = recommend_players_by_needed_position(state, build_baseline_rankings(snapshot))

    assert "QB" not in {group.position for group in groups}


def test_flex_need_waits_for_base_flex_positions() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    state = _draft_state()
    state.rosters["user_manager"].positional_counts = {"RB": 2}

    groups = recommend_players_by_needed_position(state, build_baseline_rankings(snapshot))
    positions = {group.position for group in groups}

    assert "RB" not in positions
    assert "WR" in positions
    assert "TE" in positions

    state.rosters["user_manager"].positional_counts = {"RB": 2, "WR": 2, "TE": 1}
    flex_groups = recommend_players_by_needed_position(state, build_baseline_rankings(snapshot))

    assert {"RB", "WR", "TE"} <= {group.position for group in flex_groups}

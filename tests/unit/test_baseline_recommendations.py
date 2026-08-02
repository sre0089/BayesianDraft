from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import DraftState, Player
from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.recommendations import recommend_players


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

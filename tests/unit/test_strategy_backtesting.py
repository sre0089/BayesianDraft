from bayesiandraft.backtesting import evaluate_recorded_draft_recommendations
from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.recommendations import recommend_players
from scripts.common import load_snapshot_and_draft_state


def test_strategy_backtest_replays_user_recommendations() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)

    for player_id in ["rb_001", "wr_001", "qb_001", "rb_002", "wr_002", "te_001", "wr_003"]:
        state = state.record_pick(player_id)

    recommendation = recommend_players(state, rankings)
    state = state.record_pick(recommendation.primary.player_id)

    result = evaluate_recorded_draft_recommendations(state, rankings)

    assert result.pick_count == 8
    assert result.user_pick_count == 1
    assert result.accepted_primary_count == 1
    assert result.accepted_primary_rate == 1
    assert result.final_roster_vorp >= 0
    assert result.picks[0].recommended_player_id == recommendation.primary.player_id
    assert result.picks[0].selected_vorp == result.picks[0].recommended_vorp

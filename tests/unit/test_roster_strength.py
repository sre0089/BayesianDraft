from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import score_roster_strength
from scripts.common import load_snapshot_and_draft_state


def test_roster_strength_scores_starters_plus_discounted_bench() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}

    score = score_roster_strength(
        ["qb_001", "rb_001", "rb_002", "wr_001", "wr_002", "te_001", "wr_003"],
        rankings=ranking_by_id,
        league_config=state.league_config,
        bench_discount=0.15,
    )

    assert set(score.starter_player_ids) == {
        "qb_001",
        "rb_001",
        "rb_002",
        "wr_001",
        "wr_002",
        "te_001",
        "wr_003",
    }
    assert score.bench_player_ids == []
    assert score.projected_points == score.starter_projected_points
    assert score.vorp == score.starter_vorp


def test_roster_strength_discounts_bench_and_ignores_negative_bench_vorp() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}

    score = score_roster_strength(
        [
            "qb_001",
            "qb_002",
            "rb_001",
            "rb_002",
            "rb_003",
            "wr_001",
            "wr_002",
            "wr_003",
            "te_001",
            "te_002",
            "dst_001",
            "k_001",
        ],
        rankings=ranking_by_id,
        league_config=state.league_config,
        bench_discount=0.15,
    )

    assert "qb_002" in score.bench_player_ids
    assert score.bench_projected_points > 0
    assert score.bench_vorp >= 0
    assert score.vorp >= score.starter_vorp

from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import StrategyPathSimulationConfig, analyze_user_strategy_paths
from bayesiandraft.simulation.draft import DraftSimulationConfig
from scripts.common import load_snapshot_and_draft_state


def test_strategy_path_analysis_samples_boards_before_user_pick() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)

    result = analyze_user_strategy_paths(
        state,
        rankings,
        config=StrategyPathSimulationConfig(
            simulation_count=2,
            draft_config=DraftSimulationConfig(candidate_limit=20),
        ),
    )

    assert result.paths
    assert all(path.forced_player_id for path in result.paths)
    assert all(path.average_projected_points >= 0 for path in result.paths)


def test_strategy_path_analysis_compares_forced_positions() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)
    for player_id in ["rb_001", "wr_001", "qb_001", "rb_002", "wr_002", "te_001", "wr_003"]:
        state = state.record_pick(player_id)

    result = analyze_user_strategy_paths(
        state,
        rankings,
        config=StrategyPathSimulationConfig(
            simulation_count=3,
            seed=20,
            positions=("RB", "WR", "QB", "TE"),
            draft_config=DraftSimulationConfig(candidate_limit=20),
        ),
    )

    assert result.simulation_count == 3
    assert {path.position for path in result.paths} >= {"RB", "QB", "TE"}
    assert result.paths == sorted(
        result.paths,
        key=lambda path: (-path.average_vorp, path.average_finish, path.position),
    )
    assert all(path.forced_player_id for path in result.paths)
    assert all(path.average_projected_points >= 0 for path in result.paths)
    assert all(0 <= path.top_three_rate <= 1 for path in result.paths)

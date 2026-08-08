from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import (
    LeaguePathSimulationConfig,
    StrategyPathSimulationConfig,
    analyze_league_paths,
    analyze_user_strategy_paths,
)
from bayesiandraft.simulation.draft import DraftSimulationConfig
from scripts.analyze_draft_paths import format_draft_path_report
from scripts.common import load_snapshot_and_draft_state


def test_analyze_draft_paths_formats_summary() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)
    for player_id in ["rb_001", "wr_001", "qb_001", "rb_002", "wr_002", "te_001", "wr_003"]:
        state = state.record_pick(player_id)

    draft_config = DraftSimulationConfig(candidate_limit=20)
    league_result = analyze_league_paths(
        state,
        rankings,
        config=LeaguePathSimulationConfig(
            simulation_count=3,
            seed=30,
            draft_config=draft_config,
        ),
    )
    strategy_result = analyze_user_strategy_paths(
        state,
        rankings,
        config=StrategyPathSimulationConfig(
            simulation_count=2,
            seed=40,
            draft_config=draft_config,
        ),
    )

    report = format_draft_path_report(
        league_result,
        strategy_result,
        user_manager_id=state.league_config.league.user_manager_id,
    )

    assert "After 3 simulated draft paths:" in report
    assert "Manager Results" in report
    assert "Your Team" in report
    assert "Your Strategy Outcomes" in report
    assert "RB early path" in report
    assert "Risk" in report
    assert "Best case:" in report
    assert "Top 3 rate:" in report

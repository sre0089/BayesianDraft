from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import LeaguePathSimulationConfig, analyze_league_paths
from bayesiandraft.simulation.draft import DraftSimulationConfig
from scripts.common import load_snapshot_and_draft_state


def test_league_path_analysis_summarizes_manager_outcomes() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)

    result = analyze_league_paths(
        state,
        rankings,
        config=LeaguePathSimulationConfig(
            simulation_count=4,
            seed=10,
            draft_config=DraftSimulationConfig(simulation_count=4, seed=10, candidate_limit=20),
        ),
    )

    assert result.simulation_count == 4
    assert len(result.manager_results) == 14
    assert result.manager_results[0].average_finish >= 1
    assert result.manager_results[0].average_projected_points >= 0
    assert result.manager_results[0].best_vorp >= result.manager_results[0].worst_vorp
    assert 0 <= result.user_risk.top_three_rate <= 1
    assert 0 <= result.user_risk.first_place_rate <= 1
    assert result.stopped_reasons

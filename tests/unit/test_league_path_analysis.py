from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import (
    LeaguePathProgress,
    LeaguePathSimulationConfig,
    analyze_league_paths,
)
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


def test_league_path_analysis_reports_progress() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)
    progress_events: list[LeaguePathProgress] = []

    analyze_league_paths(
        state,
        rankings,
        config=LeaguePathSimulationConfig(
            simulation_count=3,
            seed=30,
            draft_config=DraftSimulationConfig(candidate_limit=20),
        ),
        progress_callback=progress_events.append,
    )

    assert [event.completed_paths for event in progress_events] == [1, 2, 3]
    assert all(event.total_paths == 3 for event in progress_events)
    assert all(event.current_leader_id for event in progress_events)

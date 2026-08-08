from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.recommendations import build_path_bank_context
from bayesiandraft.simulation import DraftPathBank, build_path_bank
from scripts.common import load_snapshot_and_draft_state


def test_build_path_bank_creates_paths_and_lookup_tables(tmp_path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)

    path_bank = build_path_bank(
        state,
        rankings,
        snapshot_id=snapshot.snapshot.snapshot_id,
        simulation_count=3,
        seed=11,
        candidate_limit=30,
    )
    output_path = tmp_path / "path_bank.json"
    path_bank.save(output_path)
    loaded = DraftPathBank.load(output_path)

    assert len(loaded.paths) == 3
    assert loaded.metadata.snapshot_id == snapshot.snapshot.snapshot_id
    assert loaded.metadata.league_config_hash
    assert loaded.player_availability_by_pick
    assert loaded.position_value_by_pick
    assert loaded.position_dropoff_by_pick


def test_build_path_bank_reports_progress() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)
    events: list[tuple[int, int, int, str]] = []

    build_path_bank(
        state,
        rankings,
        snapshot_id=snapshot.snapshot.snapshot_id,
        simulation_count=2,
        seed=15,
        candidate_limit=30,
        progress_callback=lambda completed, total, seed, status: events.append(
            (completed, total, seed, status)
        ),
    )

    assert events[0][:3] == (1, 2, 15)
    assert events[-1] == (2, 2, 16, "indexing")


def test_path_bank_context_estimates_live_opportunity_cost() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)
    path_bank = build_path_bank(
        state,
        rankings,
        snapshot_id=snapshot.snapshot.snapshot_id,
        simulation_count=4,
        seed=21,
        candidate_limit=30,
    )

    context = build_path_bank_context(state, rankings, path_bank)

    assert context.next_user_pick == 8
    assert context.sample_quality == "exact"
    assert context.similar_path_count == 4
    assert "RB" in context.opportunity_by_position
    assert context.opportunity_by_position["RB"].opportunity_cost >= 0

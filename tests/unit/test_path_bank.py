from bayesiandraft.rankings import build_baseline_rankings
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

from pathlib import Path

from bayesiandraft.data import build_snapshot_health_report, load_player_snapshot


def test_snapshot_health_reports_fixture_coverage() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))

    report = build_snapshot_health_report(snapshot)

    assert report.player_count == 12
    assert report.projection_coverage == 1
    assert report.adp_coverage == 1
    assert "No injury records are present." in report.warnings


def test_snapshot_health_warns_about_duplicate_records() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    snapshot = snapshot.model_copy(
        update={
            "projections": [*snapshot.projections, snapshot.projections[0]],
            "adp": [*snapshot.adp, snapshot.adp[0]],
        }
    )

    report = build_snapshot_health_report(snapshot)

    assert "1 duplicate projection player references are present." in report.warnings
    assert "1 duplicate ADP player references are present." in report.warnings


def test_snapshot_health_warns_about_stale_snapshots() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))

    report = build_snapshot_health_report(snapshot, stale_after_days=0)

    assert any(warning.startswith("Snapshot is ") for warning in report.warnings)

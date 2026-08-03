from pathlib import Path

from bayesiandraft.data import build_snapshot_health_report, load_player_snapshot


def test_snapshot_health_reports_fixture_coverage() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))

    report = build_snapshot_health_report(snapshot)

    assert report.player_count == 12
    assert report.projection_coverage == 1
    assert report.adp_coverage == 1
    assert "No injury records are present." in report.warnings

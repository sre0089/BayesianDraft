from bayesiandraft.config import build_league_sanity_report, load_league_config


def test_league_sanity_report_matches_14_team_setup() -> None:
    report = build_league_sanity_report(load_league_config("configs/leagues/espn_2026.yaml"))

    assert report.team_count == 14
    assert report.user_draft_position == 8
    assert report.total_rounds == 16
    assert report.total_picks == 224
    assert "IR slots are excluded from draft length." in report.warnings

from scripts.project_status import build_project_status_report


def test_project_status_reads_milestone_tracker() -> None:
    report = build_project_status_report()

    assert report.project == "bayesiandraft"
    assert report.version == "0.1.0"
    assert report.latest_completed_milestone == 37
    assert report.completed_milestones >= 38

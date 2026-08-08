from bayesiandraft.rankings import build_baseline_rankings
from scripts.audit_model_roster_completion import (
    audit_recommended_drafts,
    format_audit_report,
)
from scripts.common import load_snapshot_and_draft_state


def test_audit_recommended_drafts_reports_roster_completion_status() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    results = audit_recommended_drafts(
        state,
        build_baseline_rankings(snapshot),
        drafts=3,
        seed=31,
        candidate_limit=40,
    )
    report = format_audit_report(results)

    assert "Model roster completion audit:" in report
    assert "seed=31" in report
    assert all(
        result.stopped_reason in {"draft_complete", "no_ranked_players"}
        for result in results
    )
    assert "Example followed-pick path" in report

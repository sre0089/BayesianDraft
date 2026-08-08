from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import build_path_bank
from scripts.audit_fast_recommendations import (
    audit_fast_recommendations,
    format_fast_recommendation_audit,
)
from scripts.common import load_snapshot_and_draft_state
from scripts.inspect_path_bank import format_path_bank_report


def test_path_bank_inspector_formats_lookup_coverage() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    path_bank = build_path_bank(
        state,
        build_baseline_rankings(snapshot),
        snapshot_id=snapshot.snapshot.snapshot_id,
        simulation_count=2,
        seed=71,
        candidate_limit=30,
    )

    report = format_path_bank_report(path_bank)

    assert "Draft path bank" in report
    assert "Lookup coverage" in report
    assert "paths: 2" in report


def test_fast_recommendation_audit_reports_latency_rows() -> None:
    snapshot, state = load_snapshot_and_draft_state()
    rankings = build_baseline_rankings(snapshot)
    path_bank = build_path_bank(
        state,
        rankings,
        snapshot_id=snapshot.snapshot.snapshot_id,
        simulation_count=2,
        seed=81,
        candidate_limit=30,
    )

    rows = audit_fast_recommendations(
        state,
        rankings,
        path_bank,
        steps=2,
        budget_ms=1000,
    )
    report = format_fast_recommendation_audit(rows)

    assert len(rows) == 2
    assert "Fast recommendation audit:" in report
    assert all(row.passed for row in rows)

from bayesiandraft.audit import (
    DecisionAuditEvent,
    append_decision_event,
    load_decision_audit,
)


def test_missing_decision_audit_loads_empty_log(tmp_path) -> None:
    audit_log = load_decision_audit(tmp_path / "audit.json")

    assert audit_log.events == []


def test_appends_and_loads_decision_event(tmp_path) -> None:
    audit_path = tmp_path / "audit.json"
    event = DecisionAuditEvent(
        event_id="pick_001",
        draft_id="draft",
        overall_pick=8,
        selected_player_id="rb_001",
        recommended_player_id="rb_001",
        alternative_player_ids=["wr_001"],
        model_versions={"recs": "baseline"},
        data_snapshot_id="synthetic_players_2026_v1",
        notes=["Accepted primary recommendation."],
    )

    updated = append_decision_event(audit_path, event)
    loaded = load_decision_audit(audit_path)

    assert updated == loaded
    assert loaded.events[0].selected_player_id == "rb_001"
    assert loaded.events[0].notes == ["Accepted primary recommendation."]

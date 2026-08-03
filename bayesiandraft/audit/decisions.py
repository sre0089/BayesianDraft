import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class DecisionAuditEvent(BaseModel):
    event_id: str
    draft_id: str
    overall_pick: int
    selected_player_id: str
    recommended_player_id: str | None = None
    alternative_player_ids: list[str] = Field(default_factory=list)
    model_versions: dict[str, str] = Field(default_factory=dict)
    data_snapshot_id: str | None = None
    notes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DecisionAuditLog(BaseModel):
    events: list[DecisionAuditEvent] = Field(default_factory=list)


def append_decision_event(path: str | Path, event: DecisionAuditEvent) -> DecisionAuditLog:
    audit_log = load_decision_audit(path)
    updated_log = DecisionAuditLog(events=[*audit_log.events, event])
    write_decision_audit(path, updated_log)
    return updated_log


def load_decision_audit(path: str | Path) -> DecisionAuditLog:
    audit_path = Path(path)
    if not audit_path.exists():
        return DecisionAuditLog()

    raw_log = json.loads(audit_path.read_text(encoding="utf-8"))
    return DecisionAuditLog.model_validate(raw_log)


def write_decision_audit(path: str | Path, audit_log: DecisionAuditLog) -> None:
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        audit_log.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from bayesiandraft.domain import (
    ADPRecord,
    DataSnapshotRecord,
    InjuryRecord,
    PlayerRecord,
    ProjectionRecord,
)


class PlayerSnapshot(BaseModel):
    snapshot: DataSnapshotRecord
    players: list[PlayerRecord]
    projections: list[ProjectionRecord]
    adp: list[ADPRecord] = Field(default_factory=list)
    injuries: list[InjuryRecord] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        player_ids = [player.player_id for player in self.players]
        if len(player_ids) != len(set(player_ids)):
            raise ValueError("players must have unique player_id values")

        known_player_ids = set(player_ids)
        projection_player_ids = {projection.player_id for projection in self.projections}
        adp_player_ids = {adp.player_id for adp in self.adp}
        injury_player_ids = {injury.player_id for injury in self.injuries}
        referenced_player_ids = projection_player_ids | adp_player_ids | injury_player_ids
        missing_player_ids = referenced_player_ids - known_player_ids
        if missing_player_ids:
            missing = ", ".join(sorted(missing_player_ids))
            raise ValueError(f"snapshot references unknown player ids: {missing}")

        if self.snapshot.row_count != len(self.players):
            raise ValueError("snapshot row_count must equal number of players")

        snapshot_ids = {
            projection.data_snapshot_id for projection in self.projections
        } | {adp.snapshot_id for adp in self.adp}
        if snapshot_ids != {self.snapshot.snapshot_id}:
            raise ValueError("records must reference the enclosing snapshot_id")


class SnapshotLoadError(ValueError):
    """Raised when a player snapshot cannot be loaded or validated."""


def load_player_snapshot(path: str | Path) -> PlayerSnapshot:
    snapshot_path = Path(path)
    try:
        raw_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SnapshotLoadError(f"Unable to read player snapshot: {snapshot_path}") from exc
    except json.JSONDecodeError as exc:
        raise SnapshotLoadError(f"Invalid JSON in player snapshot: {snapshot_path}") from exc

    try:
        return PlayerSnapshot.model_validate(raw_snapshot)
    except ValidationError as exc:
        raise SnapshotLoadError(f"Invalid player snapshot: {snapshot_path}") from exc

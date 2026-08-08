from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime

from pydantic import BaseModel

from bayesiandraft.data.snapshots import PlayerSnapshot


class SnapshotHealthReport(BaseModel):
    snapshot_id: str
    player_count: int
    projection_count: int
    adp_count: int
    injury_count: int
    projection_coverage: float
    adp_coverage: float
    warnings: list[str]


def build_snapshot_health_report(
    snapshot: PlayerSnapshot,
    *,
    stale_after_days: int = 14,
) -> SnapshotHealthReport:
    player_count = len(snapshot.players)
    projection_count = len(snapshot.projections)
    adp_count = len(snapshot.adp)
    warnings = []
    projection_coverage = _coverage(projection_count, player_count)
    adp_coverage = _coverage(adp_count, player_count)
    player_ids = {player.player_id for player in snapshot.players}
    projected_player_ids = {projection.player_id for projection in snapshot.projections}
    adp_player_ids = {adp.player_id for adp in snapshot.adp}

    if projection_coverage < 1:
        warnings.append("Projection coverage is incomplete.")
    if adp_coverage < 1:
        warnings.append("ADP coverage is incomplete.")
    if missing_projection_ids := player_ids - projected_player_ids:
        warnings.append(
            f"{len(missing_projection_ids)} players are missing projection records."
        )
    if missing_adp_ids := player_ids - adp_player_ids:
        warnings.append(f"{len(missing_adp_ids)} players are missing ADP records.")
    if duplicate_projection_count := _duplicate_record_count(
        projection.player_id for projection in snapshot.projections
    ):
        warnings.append(
            f"{duplicate_projection_count} duplicate projection player references are present."
        )
    if duplicate_adp_count := _duplicate_record_count(adp.player_id for adp in snapshot.adp):
        warnings.append(f"{duplicate_adp_count} duplicate ADP player references are present.")
    if not snapshot.injuries:
        warnings.append("No injury records are present.")
    snapshot_age_days = (datetime.now(UTC) - snapshot.snapshot.retrieval_timestamp).days
    if snapshot_age_days > stale_after_days:
        warnings.append(f"Snapshot is {snapshot_age_days} days old.")

    return SnapshotHealthReport(
        snapshot_id=snapshot.snapshot.snapshot_id,
        player_count=player_count,
        projection_count=projection_count,
        adp_count=adp_count,
        injury_count=len(snapshot.injuries),
        projection_coverage=projection_coverage,
        adp_coverage=adp_coverage,
        warnings=warnings,
    )


def _coverage(record_count: int, player_count: int) -> float:
    if player_count == 0:
        return 0
    return round(record_count / player_count, 4)


def _duplicate_record_count(player_ids: Iterable[str]) -> int:
    counts = Counter(player_ids)
    return sum(count - 1 for count in counts.values() if count > 1)

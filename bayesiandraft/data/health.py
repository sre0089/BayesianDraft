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


def build_snapshot_health_report(snapshot: PlayerSnapshot) -> SnapshotHealthReport:
    player_count = len(snapshot.players)
    projection_count = len(snapshot.projections)
    adp_count = len(snapshot.adp)
    warnings = []
    projection_coverage = _coverage(projection_count, player_count)
    adp_coverage = _coverage(adp_count, player_count)

    if projection_coverage < 1:
        warnings.append("Projection coverage is incomplete.")
    if adp_coverage < 1:
        warnings.append("ADP coverage is incomplete.")
    if not snapshot.injuries:
        warnings.append("No injury records are present.")

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

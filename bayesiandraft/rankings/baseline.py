import csv
import json
from pathlib import Path

from pydantic import BaseModel, Field

from bayesiandraft.data import PlayerSnapshot
from bayesiandraft.domain import ADPRecord, PlayerRecord, Position, ProjectionRecord

DEFAULT_STARTER_COUNTS: dict[Position, int] = {
    Position.QB: 12,
    Position.RB: 30,
    Position.WR: 30,
    Position.TE: 12,
    Position.DST: 12,
    Position.K: 12,
}

DEFAULT_REPLACEMENT_RANKS: dict[Position, int] = {
    Position.QB: 18,
    Position.RB: 42,
    Position.WR: 42,
    Position.TE: 18,
    Position.DST: 12,
    Position.K: 12,
}


class RankingConfig(BaseModel):
    starter_counts: dict[Position, int] = Field(
        default_factory=lambda: DEFAULT_STARTER_COUNTS.copy()
    )
    replacement_ranks: dict[Position, int] = Field(
        default_factory=lambda: DEFAULT_REPLACEMENT_RANKS.copy()
    )
    tier_gap_points: float = 30.0
    adp_value_scale: float = 12.0


class RankingRow(BaseModel):
    player_id: str
    full_name: str
    position: Position
    nfl_team_id: str | None
    projected_points: float
    floor: float
    median: float
    ceiling: float
    overall_rank: int
    position_rank: int
    tier: int
    replacement_points: float
    starter_threshold_points: float
    vorp: float
    value_above_starter: float
    adp: float | None
    adp_delta: float | None
    sleeper_score: float
    fade_score: float


def build_baseline_rankings(
    snapshot: PlayerSnapshot,
    config: RankingConfig | None = None,
) -> list[RankingRow]:
    ranking_config = config or RankingConfig()
    players_by_id = {player.player_id: player for player in snapshot.players}
    projections_by_player_id = _latest_projection_by_player(snapshot.projections)
    adp_by_player_id = _adp_by_player(snapshot.adp)

    position_ranked_ids = _position_ranked_player_ids(projections_by_player_id, players_by_id)
    replacement_points = _threshold_points(
        projections_by_player_id,
        position_ranked_ids,
        ranking_config.replacement_ranks,
    )
    starter_points = _threshold_points(
        projections_by_player_id,
        position_ranked_ids,
        ranking_config.starter_counts,
    )
    tiers = _assign_tiers(projections_by_player_id, players_by_id, ranking_config.tier_gap_points)

    rows = []
    for player_id, projection in projections_by_player_id.items():
        player = players_by_id[player_id]
        adp = adp_by_player_id.get(player_id)
        position_rank = position_ranked_ids[player.position].index(player_id) + 1
        replacement = replacement_points[player.position]
        starter_threshold = starter_points[player.position]
        vorp = projection.mean - replacement
        value_above_starter = projection.mean - starter_threshold
        rows.append(
            RankingRow(
                player_id=player.player_id,
                full_name=player.full_name,
                position=player.position,
                nfl_team_id=player.nfl_team_id,
                projected_points=projection.mean,
                floor=projection.lower_quantile,
                median=projection.median,
                ceiling=projection.upper_quantile,
                overall_rank=0,
                position_rank=position_rank,
                tier=tiers[player_id],
                replacement_points=replacement,
                starter_threshold_points=starter_threshold,
                vorp=vorp,
                value_above_starter=value_above_starter,
                adp=adp.overall_adp if adp else None,
                adp_delta=None,
                sleeper_score=0,
                fade_score=0,
            )
        )

    rows.sort(key=lambda row: (-row.vorp, -row.projected_points, row.full_name))
    ranked_rows = []
    for index, row in enumerate(rows, start=1):
        adp_delta = None if row.adp is None else row.adp - index
        sleeper_score = max(adp_delta or 0, 0) / ranking_config.adp_value_scale
        fade_score = max(-(adp_delta or 0), 0) / ranking_config.adp_value_scale
        ranked_rows.append(
            row.model_copy(
                update={
                    "overall_rank": index,
                    "adp_delta": adp_delta,
                    "sleeper_score": sleeper_score,
                    "fade_score": fade_score,
                }
            )
        )
    return ranked_rows


def export_rankings_json(rankings: list[RankingRow], path: str | Path) -> None:
    rows = [ranking.model_dump(mode="json") for ranking in rankings]
    Path(path).write_text(json.dumps(rows, indent=2), encoding="utf-8")


def export_rankings_csv(rankings: list[RankingRow], path: str | Path) -> None:
    if not rankings:
        Path(path).write_text("", encoding="utf-8")
        return

    rows = [ranking.model_dump(mode="json") for ranking in rankings]
    with Path(path).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _latest_projection_by_player(
    projections: list[ProjectionRecord],
) -> dict[str, ProjectionRecord]:
    return {projection.player_id: projection for projection in projections}


def _adp_by_player(adp_records: list[ADPRecord]) -> dict[str, ADPRecord]:
    return {adp.player_id: adp for adp in adp_records}


def _position_ranked_player_ids(
    projections_by_player_id: dict[str, ProjectionRecord],
    players_by_id: dict[str, PlayerRecord],
) -> dict[Position, list[str]]:
    ranked_ids: dict[Position, list[str]] = {position: [] for position in Position}
    for player_id, _projection in sorted(
        projections_by_player_id.items(),
        key=lambda item: (-item[1].mean, players_by_id[item[0]].full_name),
    ):
        ranked_ids[players_by_id[player_id].position].append(player_id)
    return ranked_ids


def _threshold_points(
    projections_by_player_id: dict[str, ProjectionRecord],
    position_ranked_ids: dict[Position, list[str]],
    rank_thresholds: dict[Position, int],
) -> dict[Position, float]:
    points: dict[Position, float] = {}
    for position in Position:
        ranked_ids = position_ranked_ids[position]
        threshold_rank = rank_thresholds[position]
        if not ranked_ids:
            points[position] = 0
            continue
        threshold_index = min(threshold_rank, len(ranked_ids)) - 1
        points[position] = projections_by_player_id[ranked_ids[threshold_index]].mean
    return points


def _assign_tiers(
    projections_by_player_id: dict[str, ProjectionRecord],
    players_by_id: dict[str, PlayerRecord],
    tier_gap_points: float,
) -> dict[str, int]:
    tiers: dict[str, int] = {}
    by_position = _position_ranked_player_ids(projections_by_player_id, players_by_id)
    for position_ranked_ids in by_position.values():
        tier = 1
        previous_points: float | None = None
        for player_id in position_ranked_ids:
            points = projections_by_player_id[player_id].mean
            if previous_points is not None and previous_points - points >= tier_gap_points:
                tier += 1
            tiers[player_id] = tier
            previous_points = points
    return tiers

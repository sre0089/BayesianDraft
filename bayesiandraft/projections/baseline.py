import random

from pydantic import BaseModel, Field

from bayesiandraft.data import PlayerSnapshot
from bayesiandraft.domain import Position, ProjectionRecord

DEFAULT_SEASON_GAMES = 17


class PlayerProjectionDistribution(BaseModel):
    player_id: str
    position: Position
    season_mean: float
    season_median: float
    season_floor: float
    season_ceiling: float
    games_played_mean: float
    weekly_mean: float
    weekly_stddev: float = Field(ge=0)
    model_version: str
    data_snapshot_id: str


class WeeklyProjectionSample(BaseModel):
    player_id: str
    week: int
    points: float
    seed: int


def build_baseline_projection_distributions(
    snapshot: PlayerSnapshot,
) -> list[PlayerProjectionDistribution]:
    players_by_id = {player.player_id: player for player in snapshot.players}
    return [
        projection_distribution_from_record(
            projection,
            position=players_by_id[projection.player_id].position,
        )
        for projection in snapshot.projections
    ]


def projection_distribution_from_record(
    projection: ProjectionRecord,
    *,
    position: Position,
) -> PlayerProjectionDistribution:
    games_played = projection.games_played_mean or DEFAULT_SEASON_GAMES
    weekly_mean = projection.mean / games_played
    season_stddev = _stddev_from_quantiles(
        lower=projection.lower_quantile,
        upper=projection.upper_quantile,
    )
    weekly_stddev = season_stddev / (games_played**0.5)

    return PlayerProjectionDistribution(
        player_id=projection.player_id,
        position=position,
        season_mean=projection.mean,
        season_median=projection.median,
        season_floor=projection.lower_quantile,
        season_ceiling=projection.upper_quantile,
        games_played_mean=games_played,
        weekly_mean=weekly_mean,
        weekly_stddev=weekly_stddev,
        model_version=projection.model_version,
        data_snapshot_id=projection.data_snapshot_id,
    )


def sample_weekly_projection(
    distribution: PlayerProjectionDistribution,
    *,
    week: int,
    seed: int,
) -> WeeklyProjectionSample:
    rng = random.Random(seed)
    points = max(rng.gauss(distribution.weekly_mean, distribution.weekly_stddev), 0)
    return WeeklyProjectionSample(
        player_id=distribution.player_id,
        week=week,
        points=round(points, 4),
        seed=seed,
    )


def sample_weekly_projections(
    distributions: list[PlayerProjectionDistribution],
    *,
    week: int,
    seed: int,
) -> list[WeeklyProjectionSample]:
    return [
        sample_weekly_projection(distribution, week=week, seed=seed + index)
        for index, distribution in enumerate(distributions)
    ]


def _stddev_from_quantiles(*, lower: float, upper: float) -> float:
    if upper <= lower:
        return 0
    return (upper - lower) / 2.563

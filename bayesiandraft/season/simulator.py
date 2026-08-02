from pydantic import BaseModel, Field, PositiveInt

from bayesiandraft.config import LeagueConfig
from bayesiandraft.projections import (
    PlayerProjectionDistribution,
    sample_weekly_projection,
)
from bayesiandraft.season.lineup import OptimizedLineup, WeeklyPlayerScore, optimize_lineup


class SeasonSimulationConfig(BaseModel):
    start_week: PositiveInt = 1
    end_week: PositiveInt = 14
    seed: int = 1


class WeeklyLineupResult(BaseModel):
    week: int
    seed: int
    lineup: OptimizedLineup


class RosterSeasonSimulation(BaseModel):
    roster_player_ids: list[str]
    start_week: int
    end_week: int
    seed: int
    weekly_results: list[WeeklyLineupResult] = Field(default_factory=list)
    total_points: float
    average_weekly_points: float


def simulate_weekly_lineup(
    roster_player_ids: list[str],
    distributions: list[PlayerProjectionDistribution],
    league_config: LeagueConfig,
    *,
    week: int,
    seed: int,
) -> WeeklyLineupResult:
    distributions_by_id = {distribution.player_id: distribution for distribution in distributions}
    weekly_scores = []
    for index, player_id in enumerate(roster_player_ids):
        distribution = distributions_by_id.get(player_id)
        if distribution is None:
            continue
        sample = sample_weekly_projection(distribution, week=week, seed=seed + index)
        weekly_scores.append(
            WeeklyPlayerScore(
                player_id=player_id,
                position=distribution.position,
                points=sample.points,
            )
        )

    return WeeklyLineupResult(
        week=week,
        seed=seed,
        lineup=optimize_lineup(weekly_scores, league_config),
    )


def simulate_roster_season(
    roster_player_ids: list[str],
    distributions: list[PlayerProjectionDistribution],
    league_config: LeagueConfig,
    *,
    config: SeasonSimulationConfig | None = None,
) -> RosterSeasonSimulation:
    simulation_config = config or SeasonSimulationConfig()
    if simulation_config.end_week < simulation_config.start_week:
        raise ValueError("end_week must be greater than or equal to start_week")

    weekly_results = [
        simulate_weekly_lineup(
            roster_player_ids,
            distributions,
            league_config,
            week=week,
            seed=simulation_config.seed + week,
        )
        for week in range(simulation_config.start_week, simulation_config.end_week + 1)
    ]
    total_points = sum(result.lineup.total_points for result in weekly_results)
    week_count = len(weekly_results)
    return RosterSeasonSimulation(
        roster_player_ids=roster_player_ids,
        start_week=simulation_config.start_week,
        end_week=simulation_config.end_week,
        seed=simulation_config.seed,
        weekly_results=weekly_results,
        total_points=round(total_points, 4),
        average_weekly_points=round(total_points / week_count if week_count else 0, 4),
    )

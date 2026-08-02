from collections.abc import Iterable
from dataclasses import dataclass, field

from bayesiandraft.config import LeagueConfig
from bayesiandraft.config.league import FieldGoalBucket, RangeScoringBucket


@dataclass(frozen=True)
class PassingStats:
    yards: float = 0
    touchdowns: int = 0
    interceptions: int = 0
    two_point_conversions: int = 0


@dataclass(frozen=True)
class RushingStats:
    yards: float = 0
    touchdowns: int = 0
    two_point_conversions: int = 0


@dataclass(frozen=True)
class ReceivingStats:
    yards: float = 0
    receptions: int = 0
    touchdowns: int = 0
    two_point_conversions: int = 0


@dataclass(frozen=True)
class KickingStats:
    pats_made: int = 0
    field_goals_missed: int = 0
    field_goals_made_yards: tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DefenseSpecialTeamsStats:
    kickoff_return_touchdowns: int = 0
    punt_return_touchdowns: int = 0
    interception_return_touchdowns: int = 0
    fumble_return_touchdowns: int = 0
    blocked_punt_or_field_goal_return_touchdowns: int = 0
    two_point_returns: int = 0
    one_point_safeties: int = 0
    sacks: int = 0
    blocked_punts_pats_or_field_goals: int = 0
    interceptions: int = 0
    fumble_recoveries: int = 0
    safeties: int = 0
    points_allowed: int | None = None
    yards_allowed: int | None = None


@dataclass(frozen=True)
class OffensiveStats:
    passing: PassingStats = field(default_factory=PassingStats)
    rushing: RushingStats = field(default_factory=RushingStats)
    receiving: ReceivingStats = field(default_factory=ReceivingStats)


def score_passing(stats: PassingStats, config: LeagueConfig) -> float:
    scoring = config.scoring.passing
    return (
        stats.yards * scoring.yards
        + stats.touchdowns * scoring.touchdown
        + stats.interceptions * scoring.interception
        + stats.two_point_conversions * scoring.two_point_conversion
    )


def score_rushing(stats: RushingStats, config: LeagueConfig) -> float:
    scoring = config.scoring.rushing
    return (
        stats.yards * scoring.yards
        + stats.touchdowns * scoring.touchdown
        + stats.two_point_conversions * scoring.two_point_conversion
    )


def score_receiving(stats: ReceivingStats, config: LeagueConfig) -> float:
    scoring = config.scoring.receiving
    return (
        stats.yards * scoring.yards
        + stats.receptions * scoring.reception
        + stats.touchdowns * scoring.touchdown
        + stats.two_point_conversions * scoring.two_point_conversion
    )


def score_kicking(stats: KickingStats, config: LeagueConfig) -> float:
    scoring = config.scoring.kicking
    field_goal_points = sum(
        _score_field_goal(yards, scoring.field_goal_made) for yards in stats.field_goals_made_yards
    )
    return (
        stats.pats_made * scoring.pat_made
        + stats.field_goals_missed * scoring.field_goal_missed
        + field_goal_points
    )


def score_defense_special_teams(
    stats: DefenseSpecialTeamsStats,
    config: LeagueConfig,
) -> float:
    scoring = config.scoring.defense_special_teams
    total = (
        stats.kickoff_return_touchdowns * scoring.touchdowns["kickoff_return"]
        + stats.punt_return_touchdowns * scoring.touchdowns["punt_return"]
        + stats.interception_return_touchdowns * scoring.touchdowns["interception_return"]
        + stats.fumble_return_touchdowns * scoring.touchdowns["fumble_return"]
        + stats.blocked_punt_or_field_goal_return_touchdowns
        * scoring.touchdowns["blocked_punt_or_field_goal_return"]
        + stats.two_point_returns * scoring.returns["two_point_return"]
        + stats.one_point_safeties * scoring.returns["one_point_safety"]
        + stats.sacks * scoring.events["sack"]
        + stats.blocked_punts_pats_or_field_goals
        * scoring.events["blocked_punt_pat_or_field_goal"]
        + stats.interceptions * scoring.events["interception"]
        + stats.fumble_recoveries * scoring.events["fumble_recovery"]
        + stats.safeties * scoring.events["safety"]
    )

    if stats.points_allowed is not None:
        total += _score_range(stats.points_allowed, scoring.points_allowed)

    if stats.yards_allowed is not None:
        total += _score_range(stats.yards_allowed, scoring.yards_allowed)

    return total


def score_offense(stats: OffensiveStats, config: LeagueConfig) -> float:
    return (
        score_passing(stats.passing, config)
        + score_rushing(stats.rushing, config)
        + score_receiving(stats.receiving, config)
    )


def _score_field_goal(yards: int, buckets: Iterable[FieldGoalBucket]) -> float:
    if yards < 0:
        raise ValueError("field goal yards cannot be negative")

    for bucket in buckets:
        if bucket.contains(yards):
            return bucket.points

    raise ValueError(f"No field goal scoring bucket for {yards} yards")


def _score_range(value: int, buckets: Iterable[RangeScoringBucket]) -> float:
    if value < 0:
        raise ValueError("scoring range value cannot be negative")

    for bucket in buckets:
        if bucket.contains(value):
            return bucket.points

    raise ValueError(f"No scoring bucket for value {value}")

from collections.abc import Iterator
from pathlib import Path

import pytest

from bayesiandraft.config import LeagueConfig, load_league_config
from bayesiandraft.scoring import (
    DefenseSpecialTeamsStats,
    KickingStats,
    OffensiveStats,
    PassingStats,
    ReceivingStats,
    RushingStats,
    score_defense_special_teams,
    score_kicking,
    score_offense,
    score_passing,
    score_receiving,
    score_rushing,
)


@pytest.fixture(scope="module")
def league_config() -> Iterator[LeagueConfig]:
    yield load_league_config(Path("configs/leagues/espn_2026.yaml"))


def test_scores_passing_stats(league_config: LeagueConfig) -> None:
    stats = PassingStats(yards=250, touchdowns=2, interceptions=1, two_point_conversions=1)

    assert score_passing(stats, league_config) == 18


def test_scores_rushing_stats(league_config: LeagueConfig) -> None:
    stats = RushingStats(yards=83, touchdowns=1, two_point_conversions=1)

    assert score_rushing(stats, league_config) == pytest.approx(16.3)


def test_scores_receiving_stats_with_full_ppr(league_config: LeagueConfig) -> None:
    stats = ReceivingStats(yards=75, receptions=6, touchdowns=1, two_point_conversions=1)

    assert score_receiving(stats, league_config) == pytest.approx(21.5)


def test_scores_combined_offensive_stat_line(league_config: LeagueConfig) -> None:
    stats = OffensiveStats(
        passing=PassingStats(yards=40, touchdowns=1),
        rushing=RushingStats(yards=20),
        receiving=ReceivingStats(yards=30, receptions=3),
    )

    assert score_offense(stats, league_config) == pytest.approx(13.6)


@pytest.mark.parametrize(
    ("yards", "expected_points"),
    [
        (0, 3),
        (39, 3),
        (40, 4),
        (49, 4),
        (50, 5),
        (59, 5),
        (60, 6),
        (70, 6),
    ],
)
def test_scores_field_goal_bucket_boundaries(
    league_config: LeagueConfig,
    yards: int,
    expected_points: int,
) -> None:
    stats = KickingStats(field_goals_made_yards=(yards,))

    assert score_kicking(stats, league_config) == expected_points


def test_scores_kicking_negative_events(league_config: LeagueConfig) -> None:
    stats = KickingStats(pats_made=2, field_goals_missed=1, field_goals_made_yards=(61,))

    assert score_kicking(stats, league_config) == 7


@pytest.mark.parametrize(
    ("points_allowed", "expected_points"),
    [
        (0, 5),
        (1, 4),
        (6, 4),
        (7, 3),
        (13, 3),
        (14, 1),
        (17, 1),
        (18, 0),
        (27, 0),
        (28, -1),
        (34, -1),
        (35, -3),
        (45, -3),
        (46, -5),
        (60, -5),
    ],
)
def test_scores_dst_points_allowed_bucket_boundaries(
    league_config: LeagueConfig,
    points_allowed: int,
    expected_points: int,
) -> None:
    stats = DefenseSpecialTeamsStats(points_allowed=points_allowed)

    assert score_defense_special_teams(stats, league_config) == expected_points


@pytest.mark.parametrize(
    ("yards_allowed", "expected_points"),
    [
        (0, 5),
        (99, 5),
        (100, 3),
        (199, 3),
        (200, 2),
        (299, 2),
        (300, 0),
        (349, 0),
        (350, -1),
        (399, -1),
        (400, -3),
        (449, -3),
        (450, -5),
        (499, -5),
        (500, -6),
        (549, -6),
        (550, -7),
        (700, -7),
    ],
)
def test_scores_dst_yards_allowed_bucket_boundaries(
    league_config: LeagueConfig,
    yards_allowed: int,
    expected_points: int,
) -> None:
    stats = DefenseSpecialTeamsStats(yards_allowed=yards_allowed)

    assert score_defense_special_teams(stats, league_config) == expected_points


def test_scores_dst_events_and_touchdowns(league_config: LeagueConfig) -> None:
    stats = DefenseSpecialTeamsStats(
        kickoff_return_touchdowns=1,
        punt_return_touchdowns=1,
        interception_return_touchdowns=1,
        fumble_return_touchdowns=1,
        blocked_punt_or_field_goal_return_touchdowns=1,
        two_point_returns=1,
        one_point_safeties=1,
        sacks=3,
        blocked_punts_pats_or_field_goals=1,
        interceptions=2,
        fumble_recoveries=1,
        safeties=1,
    )

    assert score_defense_special_teams(stats, league_config) == 46


def test_rejects_negative_bucket_values(league_config: LeagueConfig) -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        score_kicking(KickingStats(field_goals_made_yards=(-1,)), league_config)

    with pytest.raises(ValueError, match="cannot be negative"):
        score_defense_special_teams(
            DefenseSpecialTeamsStats(points_allowed=-1),
            league_config,
        )

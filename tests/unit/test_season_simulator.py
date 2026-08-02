from pathlib import Path

import pytest

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.domain import Position
from bayesiandraft.projections import build_baseline_projection_distributions
from bayesiandraft.season import (
    SeasonSimulationConfig,
    WeeklyPlayerScore,
    optimize_lineup,
    simulate_roster_season,
    simulate_weekly_lineup,
)


def _league_config():
    return load_league_config("configs/leagues/espn_2026.yaml")


def _distributions():
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    return build_baseline_projection_distributions(snapshot)


def test_optimize_lineup_fills_fixed_slots_and_flex() -> None:
    lineup = optimize_lineup(
        [
            WeeklyPlayerScore(player_id="qb", position=Position.QB, points=20),
            WeeklyPlayerScore(player_id="rb1", position=Position.RB, points=15),
            WeeklyPlayerScore(player_id="rb2", position=Position.RB, points=14),
            WeeklyPlayerScore(player_id="rb3", position=Position.RB, points=13),
            WeeklyPlayerScore(player_id="wr1", position=Position.WR, points=12),
            WeeklyPlayerScore(player_id="wr2", position=Position.WR, points=11),
            WeeklyPlayerScore(player_id="te", position=Position.TE, points=10),
            WeeklyPlayerScore(player_id="dst", position=Position.DST, points=9),
            WeeklyPlayerScore(player_id="k", position=Position.K, points=8),
        ],
        _league_config(),
    )

    assert lineup.total_points == 112
    assert {starter.player_id for starter in lineup.starters} == {
        "qb",
        "rb1",
        "rb2",
        "rb3",
        "wr1",
        "wr2",
        "te",
        "dst",
        "k",
    }
    assert not lineup.open_slots


def test_weekly_lineup_simulation_is_seeded() -> None:
    roster = [distribution.player_id for distribution in _distributions()]

    first = simulate_weekly_lineup(roster, _distributions(), _league_config(), week=1, seed=5)
    second = simulate_weekly_lineup(roster, _distributions(), _league_config(), week=1, seed=5)

    assert first == second
    assert first.lineup.total_points > 0


def test_roster_season_simulation_summarizes_weeks() -> None:
    roster = [distribution.player_id for distribution in _distributions()]

    result = simulate_roster_season(
        roster,
        _distributions(),
        _league_config(),
        config=SeasonSimulationConfig(start_week=1, end_week=3, seed=9),
    )

    assert len(result.weekly_results) == 3
    assert result.total_points > 0
    assert result.average_weekly_points == round(result.total_points / 3, 4)


def test_roster_season_rejects_invalid_week_range() -> None:
    with pytest.raises(ValueError, match="end_week"):
        simulate_roster_season(
            [],
            [],
            _league_config(),
            config=SeasonSimulationConfig(start_week=4, end_week=3),
        )

from datetime import UTC, datetime
from pathlib import Path

from bayesiandraft.data import load_player_snapshot
from bayesiandraft.domain import InjuryRecord
from bayesiandraft.projections import (
    build_baseline_projection_distributions,
    estimate_all_games_played,
    estimate_games_played,
)


def _distributions():
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    return build_baseline_projection_distributions(snapshot)


def test_games_played_defaults_to_full_availability_without_injury() -> None:
    distribution = _distributions()[0]

    estimate = estimate_games_played(distribution, [])

    assert estimate.availability_probability == 1
    assert estimate.adjusted_games_played == estimate.base_games_played
    assert estimate.risk_label == "low"


def test_games_played_uses_latest_injury_status_and_confidence() -> None:
    distribution = _distributions()[0]
    injuries = [
        InjuryRecord(
            injury_id="old",
            player_id=distribution.player_id,
            report_date=datetime(2026, 8, 1, tzinfo=UTC).date(),
            status="questionable",
            source="fixture",
            source_timestamp=datetime(2026, 8, 1, tzinfo=UTC),
            confidence=1,
        ),
        InjuryRecord(
            injury_id="new",
            player_id=distribution.player_id,
            report_date=datetime(2026, 8, 2, tzinfo=UTC).date(),
            status="out",
            source="fixture",
            source_timestamp=datetime(2026, 8, 2, tzinfo=UTC),
            confidence=1,
        ),
    ]

    estimate = estimate_games_played(distribution, injuries)

    assert estimate.availability_probability == 0
    assert estimate.adjusted_season_mean == 0
    assert estimate.risk_label == "high"


def test_estimates_all_games_played_records() -> None:
    distributions = _distributions()

    estimates = estimate_all_games_played(distributions, [])

    assert len(estimates) == len(distributions)
    assert {estimate.player_id for estimate in estimates} == {
        distribution.player_id for distribution in distributions
    }

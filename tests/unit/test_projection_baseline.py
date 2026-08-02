from pathlib import Path

from bayesiandraft.data import load_player_snapshot
from bayesiandraft.projections import (
    build_baseline_projection_distributions,
    sample_weekly_projection,
    sample_weekly_projections,
)


def test_builds_projection_distributions_from_snapshot() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))

    distributions = build_baseline_projection_distributions(snapshot)

    assert len(distributions) == len(snapshot.projections)
    assert distributions[0].data_snapshot_id == snapshot.snapshot.snapshot_id
    assert distributions[0].weekly_mean > 0
    assert distributions[0].weekly_stddev >= 0


def test_weekly_projection_sampling_is_seeded() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    distribution = build_baseline_projection_distributions(snapshot)[0]

    first = sample_weekly_projection(distribution, week=1, seed=42)
    second = sample_weekly_projection(distribution, week=1, seed=42)

    assert first == second
    assert first.points >= 0


def test_weekly_projection_sampling_uses_unique_player_seeds() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    distributions = build_baseline_projection_distributions(snapshot)

    samples = sample_weekly_projections(distributions, week=3, seed=10)

    assert {sample.player_id for sample in samples} == {
        distribution.player_id for distribution in distributions
    }
    assert [sample.seed for sample in samples[:3]] == [10, 11, 12]

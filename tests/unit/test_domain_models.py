from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from bayesiandraft.domain import (
    ADPRecord,
    DataSnapshotRecord,
    InjuryRecord,
    PlayerRecord,
    Position,
    ProjectionRecord,
    RecommendationRecord,
)


def test_player_record_validates_position_and_bye_week() -> None:
    player = PlayerRecord(
        player_id="player_001",
        full_name="Example Receiver",
        position=Position.WR,
        bye_week=8,
    )

    assert player.position == Position.WR

    with pytest.raises(ValidationError, match="bye_week"):
        PlayerRecord(player_id="bad", full_name="Bad Bye", position=Position.RB, bye_week=22)


def test_projection_requires_week_for_weekly_scope() -> None:
    with pytest.raises(ValidationError, match="week is required"):
        ProjectionRecord(
            projection_id="projection_001",
            player_id="player_001",
            season=2026,
            scope="week",
            mean=10,
            median=9,
            lower_quantile=4,
            upper_quantile=16,
            model_version="baseline",
            data_snapshot_id="snapshot_001",
            generated_at=datetime.now(UTC),
        )


def test_projection_rejects_inverted_quantiles() -> None:
    with pytest.raises(ValidationError, match="upper_quantile"):
        ProjectionRecord(
            projection_id="projection_001",
            player_id="player_001",
            season=2026,
            mean=10,
            median=9,
            lower_quantile=18,
            upper_quantile=16,
            model_version="baseline",
            data_snapshot_id="snapshot_001",
            generated_at=datetime.now(UTC),
        )


def test_probability_fields_are_bounded() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 1"):
        RecommendationRecord(
            recommendation_id="rec_001",
            draft_state_id="draft_001",
            candidate_player_id="player_001",
            rank=1,
            expected_utility=12,
            playoff_probability=0.5,
            championship_probability=1.2,
            next_pick_availability=0.2,
            confidence=0.7,
            explanation_components=["test"],
            model_version="baseline",
            generated_at=datetime.now(UTC),
        )


def test_adp_and_snapshot_records_validate() -> None:
    adp = ADPRecord(
        adp_id="adp_001",
        player_id="player_001",
        source="synthetic",
        format="redraft",
        scoring="full_ppr",
        date=date(2026, 8, 1),
        overall_adp=12.4,
        position_adp=5,
        rank=12,
        snapshot_id="snapshot_001",
    )
    snapshot = DataSnapshotRecord(
        snapshot_id="snapshot_001",
        dataset_name="baseline_players",
        source="synthetic",
        retrieval_timestamp=datetime.now(UTC),
        season=2026,
        checksum="abc123",
        processed_path="data/fixtures/baseline_players_2026.json",
        schema_version="1",
        preprocessing_version="manual",
        license_notes="Synthetic fixture data.",
        row_count=1,
    )

    assert adp.snapshot_id == snapshot.snapshot_id


def test_injury_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        InjuryRecord(
            injury_id="injury_001",
            player_id="player_001",
            report_date=date(2026, 8, 1),
            status="healthy",
            source="synthetic",
            source_timestamp=datetime.now(UTC),
            confidence=-0.1,
        )

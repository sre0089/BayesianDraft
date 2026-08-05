from datetime import UTC, datetime
from pathlib import Path

import pytest

from bayesiandraft.config import load_league_config
from bayesiandraft.data import (
    SnapshotImportError,
    SnapshotImportOptions,
    import_stat_projection_csv,
)


def test_imports_stat_projection_csv_with_scored_points(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    csv_path.write_text(
        "\n".join(
            [
                "player_id,full_name,position,team,passing_yards,passing_touchdowns,"
                "interceptions_thrown,rushing_yards,rushing_touchdowns,receptions,"
                "receiving_yards,receiving_touchdowns,overall_adp,bye_week",
                "qb_001,Example QB One,QB,AAA,4000,30,10,250,3,0,0,0,25,6",
                "rb_001,Example RB One,RB,BBB,0,0,0,1100,9,55,430,3,5,8",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    snapshot = import_stat_projection_csv(
        csv_path,
        options=_options(),
        processed_path=tmp_path / "snapshot.json",
        league_config=load_league_config("configs/leagues/espn_2026.yaml"),
    )

    assert snapshot.snapshot.row_count == 2
    assert snapshot.projections[0].mean == pytest.approx(303)
    assert snapshot.projections[1].mean == pytest.approx(280)
    assert snapshot.adp[0].overall_adp == 25
    assert snapshot.players[1].bye_week == 8


def test_imports_kicker_and_dst_stat_projection_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    csv_path.write_text(
        "\n".join(
            [
                "player_id,full_name,position,pat_made,field_goal_missed,fg_made_0_39,"
                "fg_made_40_49,fg_made_50_59,fg_made_60_plus,dst_touchdowns,dst_sacks,"
                "dst_interceptions,dst_fumble_recoveries,dst_safeties,dst_blocked_kicks",
                "k_001,Example K One,K,40,2,10,8,5,1,0,0,0,0,0,0",
                "dst_001,Example DST One,DST,0,0,0,0,0,0,3,45,12,8,1,4",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    snapshot = import_stat_projection_csv(
        csv_path,
        options=_options(),
        processed_path=tmp_path / "snapshot.json",
        league_config=load_league_config("configs/leagues/espn_2026.yaml"),
    )

    assert snapshot.projections[0].mean == pytest.approx(131)
    assert snapshot.projections[1].mean == pytest.approx(113)


def test_stat_projection_importer_rejects_empty_stat_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "stats.csv"
    csv_path.write_text(
        "player_id,full_name,position\nrb_001,Example RB One,RB\n",
        encoding="utf-8",
    )

    with pytest.raises(SnapshotImportError, match="zero projected points"):
        import_stat_projection_csv(
            csv_path,
            options=_options(),
            processed_path=tmp_path / "snapshot.json",
            league_config=load_league_config("configs/leagues/espn_2026.yaml"),
        )


def _options() -> SnapshotImportOptions:
    return SnapshotImportOptions(
        snapshot_id="stat_projection_2026_v1",
        season=2026,
        source="local-stat-test",
        retrieval_timestamp=datetime(2026, 8, 5, tzinfo=UTC),
        dataset_name="stat_projection_test",
        preprocessing_version="stat_projection_csv_v1",
    )

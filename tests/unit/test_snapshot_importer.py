import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from bayesiandraft.data import (
    SnapshotImportError,
    SnapshotImportOptions,
    import_player_snapshot_csv,
    write_player_snapshot,
)


def test_imports_projection_csv_snapshot(tmp_path: Path) -> None:
    csv_path = tmp_path / "players.csv"
    csv_path.write_text(
        "\n".join(
            [
                "player_id,full_name,position,team,projected_points,median_points,"
                "floor_points,ceiling_points,games_played,overall_adp,position_adp,"
                "adp_rank,bye_week",
                "rb_001,Example RB One,RB,CCC,285,280,220,340,16.5,5,1,5,8",
                "wr_001,Example WR One,WR,FFF,270,268,210,325,16,8,1,8,9",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "snapshot.json"

    snapshot = import_player_snapshot_csv(
        csv_path,
        options=_options(),
        processed_path=output_path,
    )

    assert snapshot.snapshot.snapshot_id == "local_2026_v1"
    assert snapshot.snapshot.row_count == 2
    assert snapshot.snapshot.raw_path == str(csv_path)
    assert snapshot.snapshot.processed_path == str(output_path)
    assert [player.player_id for player in snapshot.players] == ["rb_001", "wr_001"]
    assert snapshot.projections[0].mean == 285
    assert snapshot.projections[0].lower_quantile == 220
    assert snapshot.adp[0].overall_adp == 5
    assert snapshot.adp[0].rank == 5


def test_importer_uses_projection_defaults(tmp_path: Path) -> None:
    csv_path = tmp_path / "players.csv"
    csv_path.write_text(
        "player_id,full_name,position,projected_points\n"
        "qb_001,Example QB One,QB,300\n",
        encoding="utf-8",
    )

    snapshot = import_player_snapshot_csv(
        csv_path,
        options=_options(),
        processed_path=tmp_path / "snapshot.json",
    )

    projection = snapshot.projections[0]
    assert projection.median == 300
    assert projection.lower_quantile == 240
    assert projection.upper_quantile == 360
    assert snapshot.adp == []


def test_writes_imported_snapshot_json(tmp_path: Path) -> None:
    csv_path = tmp_path / "players.csv"
    csv_path.write_text(
        "player_id,full_name,position,projected_points\n"
        "te_001,Example TE One,TE,180\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "snapshot.json"
    snapshot = import_player_snapshot_csv(
        csv_path,
        options=_options(),
        processed_path=output_path,
    )

    write_player_snapshot(snapshot, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["snapshot"]["snapshot_id"] == "local_2026_v1"
    assert payload["players"][0]["player_id"] == "te_001"


def test_importer_rejects_missing_required_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "players.csv"
    csv_path.write_text(
        "player_id,full_name,position\nrb_001,Example RB One,RB\n",
        encoding="utf-8",
    )

    with pytest.raises(SnapshotImportError, match="missing required columns"):
        import_player_snapshot_csv(
            csv_path,
            options=_options(),
            processed_path=tmp_path / "snapshot.json",
        )


def test_importer_rejects_duplicate_player_ids(tmp_path: Path) -> None:
    csv_path = tmp_path / "players.csv"
    csv_path.write_text(
        "player_id,full_name,position,projected_points\n"
        "rb_001,Example RB One,RB,285\n"
        "rb_001,Example RB Duplicate,RB,280\n",
        encoding="utf-8",
    )

    with pytest.raises(SnapshotImportError, match="duplicate player_id"):
        import_player_snapshot_csv(
            csv_path,
            options=_options(),
            processed_path=tmp_path / "snapshot.json",
        )


def test_importer_rejects_bad_position(tmp_path: Path) -> None:
    csv_path = tmp_path / "players.csv"
    csv_path.write_text(
        "player_id,full_name,position,projected_points\n"
        "idp_001,Example IDP,LB,120\n",
        encoding="utf-8",
    )

    with pytest.raises(SnapshotImportError, match="invalid player record"):
        import_player_snapshot_csv(
            csv_path,
            options=_options(),
            processed_path=tmp_path / "snapshot.json",
        )


def test_importer_rejects_bad_numeric_value(tmp_path: Path) -> None:
    csv_path = tmp_path / "players.csv"
    csv_path.write_text(
        "player_id,full_name,position,projected_points\n"
        "rb_001,Example RB One,RB,not-a-number\n",
        encoding="utf-8",
    )

    with pytest.raises(SnapshotImportError, match="invalid number"):
        import_player_snapshot_csv(
            csv_path,
            options=_options(),
            processed_path=tmp_path / "snapshot.json",
        )


def _options() -> SnapshotImportOptions:
    return SnapshotImportOptions(
        snapshot_id="local_2026_v1",
        season=2026,
        source="local-test",
        retrieval_timestamp=datetime(2026, 8, 4, tzinfo=UTC),
    )

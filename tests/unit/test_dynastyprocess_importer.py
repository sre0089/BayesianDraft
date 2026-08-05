from datetime import UTC, datetime
from pathlib import Path

import pytest

from bayesiandraft.data import (
    SnapshotImportError,
    SnapshotImportOptions,
    import_dynastyprocess_rankings_csv,
)


def test_imports_dynastyprocess_rankings_snapshot(tmp_path: Path) -> None:
    csv_path = tmp_path / "db_fpecr_latest.csv"
    csv_path.write_text(
        "\n".join(
            [
                "fp_page,page_type,ecr_type,player,id,pos,team,ecr,sd,best,worst,"
                "bye,mergename,scrape_date,tm",
                "/rankings,redraft-overall,ro,Real RB One,1001,RB,ATL,1,0,1,1,12,"
                "Real RB One,2026-08-01,ATL",
                "/rankings,redraft-overall,ro,Real WR One,1002,WR,CIN,2,0,2,2,10,"
                "Real WR One,2026-08-01,CIN",
                "/rankings,redraft-overall,ro,Real QB One,1003,QB,BUF,3,0,3,3,7,"
                "Real QB One,2026-08-01,BUF",
                "/rankings,redraft-overall,ro,Real TE One,1005,TE,FA,4,0,4,4,NA,"
                "Real TE One,2026-08-01,FA",
                "/rankings,redraft-idp,ro,Ignored Defender,9999,LB,NYJ,1,0,1,1,9,"
                "Ignored Defender,2026-08-01,NYJ",
                "/rankings,redraft-overall,ro,Old RB,1004,RB,DAL,1,0,1,1,8,"
                "Old RB,2026-07-01,DAL",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    snapshot = import_dynastyprocess_rankings_csv(
        csv_path,
        options=_options(),
        processed_path=tmp_path / "snapshot.json",
    )

    assert snapshot.snapshot.row_count == 4
    assert snapshot.players[0].full_name == "Real RB One"
    assert snapshot.players[0].player_id == "fp_1001"
    assert snapshot.players[0].source_player_ids == {"fantasypros": "1001"}
    assert snapshot.projections[0].mean == 300
    assert snapshot.adp[0].overall_adp == 1
    assert snapshot.adp[0].position_adp == 1
    assert snapshot.players[3].bye_week is None
    assert {player.position.value for player in snapshot.players} == {"QB", "RB", "TE", "WR"}


def test_dynastyprocess_importer_rejects_missing_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("player,id,pos\nReal RB One,1001,RB\n", encoding="utf-8")

    with pytest.raises(SnapshotImportError, match="missing required columns"):
        import_dynastyprocess_rankings_csv(
            csv_path,
            options=_options(),
            processed_path=tmp_path / "snapshot.json",
        )


def test_dynastyprocess_importer_rejects_missing_page_type(tmp_path: Path) -> None:
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text(
        "page_type,player,id,pos,team,ecr,bye,scrape_date\n"
        "dynasty-overall,Real RB One,1001,RB,ATL,1,12,2026-08-01\n",
        encoding="utf-8",
    )

    with pytest.raises(SnapshotImportError, match="no supported rankings rows"):
        import_dynastyprocess_rankings_csv(
            csv_path,
            options=_options(),
            processed_path=tmp_path / "snapshot.json",
        )


def _options() -> SnapshotImportOptions:
    return SnapshotImportOptions(
        snapshot_id="dynastyprocess_2026_v1",
        season=2026,
        source="DynastyProcess FantasyPros ECR",
        retrieval_timestamp=datetime(2026, 8, 4, tzinfo=UTC),
        dataset_name="dynastyprocess_rankings",
        preprocessing_version="dynastyprocess_ecr_proxy_v1",
        license_notes="Public DynastyProcess data with FantasyPros ECR rankings.",
        source_url="https://github.com/dynastyprocess/data",
    )

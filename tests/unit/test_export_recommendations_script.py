import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from bayesiandraft.data import (
    SnapshotImportOptions,
    import_player_snapshot_csv,
    write_player_snapshot,
)


def test_export_recommendations_script_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "recommendations.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_recommendations.py",
            "--out",
            str(output_path),
            "--scenario",
            "data/fixtures/rehearsal_user_pick_8.json",
        ],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "."},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["primary"]["player_id"]
    assert payload["alternatives"]


def test_export_recommendations_script_uses_snapshot_path(tmp_path: Path) -> None:
    snapshot_path = _write_imported_snapshot(tmp_path)
    output_path = tmp_path / "recommendations.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_recommendations.py",
            "--snapshot",
            str(snapshot_path),
            "--out",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "."},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["primary"]["player_id"].startswith("local_")


def _write_imported_snapshot(tmp_path: Path) -> Path:
    csv_path = tmp_path / "players.csv"
    csv_path.write_text(
        "player_id,full_name,position,projected_points,overall_adp\n"
        "local_rb_001,Local RB One,RB,250,10\n"
        "local_wr_001,Local WR One,WR,210,20\n",
        encoding="utf-8",
    )
    snapshot_path = tmp_path / "snapshot.json"
    snapshot = import_player_snapshot_csv(
        csv_path,
        options=SnapshotImportOptions(
            snapshot_id="local_recommendations_2026_v1",
            season=2026,
            source="local-test",
            retrieval_timestamp=datetime(2026, 8, 4, tzinfo=UTC),
        ),
        processed_path=snapshot_path,
    )
    write_player_snapshot(snapshot, snapshot_path)
    return snapshot_path

import json
import os
import subprocess
import sys
from pathlib import Path

from bayesiandraft.data import load_ingestion_manifest, load_player_snapshot


def test_import_snapshot_script_writes_snapshot_and_manifest(tmp_path: Path) -> None:
    csv_path = tmp_path / "players.csv"
    csv_path.write_text(
        "player_id,full_name,position,projected_points,overall_adp\n"
        "rb_001,Example RB One,RB,285,5\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "snapshot.json"
    manifest_path = tmp_path / "manifest.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/import_snapshot.py",
            "--players",
            str(csv_path),
            "--out",
            str(output_path),
            "--manifest-out",
            str(manifest_path),
            "--snapshot-id",
            "local_2026_v1",
            "--season",
            "2026",
            "--source",
            "local-test",
            "--retrieved-at",
            "2026-08-04T00:00:00Z",
        ],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "."},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    stdout_payload = json.loads(result.stdout)
    assert stdout_payload["snapshot"]["snapshot_id"] == "local_2026_v1"
    assert load_player_snapshot(output_path).players[0].player_id == "rb_001"

    manifest = load_ingestion_manifest(manifest_path)
    assert manifest.snapshot_id == "local_2026_v1"
    assert manifest.row_count == 1

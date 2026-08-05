import json
import os
import subprocess
import sys
from pathlib import Path

from bayesiandraft.data import load_ingestion_manifest


def test_pull_dynastyprocess_script_writes_snapshot_and_manifest(tmp_path: Path) -> None:
    source_path = tmp_path / "source.csv"
    source_path.write_text(
        "\n".join(
            [
                "page_type,player,id,pos,team,ecr,bye,scrape_date,tm",
                "redraft-overall,Real RB One,1001,RB,ATL,1,12,2026-08-01,ATL",
                "redraft-overall,Real WR One,1002,WR,CIN,2,10,2026-08-01,CIN",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    raw_path = tmp_path / "raw.csv"
    output_path = tmp_path / "snapshot.json"
    manifest_path = tmp_path / "manifest.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/pull_dynastyprocess.py",
            "--source-url",
            source_path.as_uri(),
            "--raw-out",
            str(raw_path),
            "--out",
            str(output_path),
            "--manifest-out",
            str(manifest_path),
            "--snapshot-id",
            "dynastyprocess_test",
            "--season",
            "2026",
        ],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "."},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["snapshot"]["snapshot_id"] == "dynastyprocess_test"
    assert payload["players"][0]["full_name"] == "Real RB One"
    assert load_ingestion_manifest(manifest_path).row_count == 2

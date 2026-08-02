import json
import os
import subprocess
import sys
from pathlib import Path


def test_export_baseline_rankings_script_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "rankings.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_baseline_rankings.py",
            "--out",
            str(output_path),
            "--format",
            "json",
        ],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "."},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    rows = json.loads(output_path.read_text(encoding="utf-8"))
    assert rows[0]["overall_rank"] == 1

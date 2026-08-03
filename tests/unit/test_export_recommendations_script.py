import json
import os
import subprocess
import sys
from pathlib import Path


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

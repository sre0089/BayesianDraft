import os
import subprocess
import sys


def test_verify_ingestion_manifest_script_accepts_baseline_manifest() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify_ingestion_manifest.py",
            "data/manifests/baseline_players_2026.json",
        ],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "."},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "verified synthetic_players_2026_v1" in result.stdout

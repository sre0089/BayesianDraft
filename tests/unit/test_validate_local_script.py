import os
import subprocess
import sys


def test_validate_local_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_local.py"],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": ".:apps/api/src"},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "local validation ok" in result.stdout

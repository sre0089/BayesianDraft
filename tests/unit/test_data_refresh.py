import os
import subprocess
import sys

from bayesiandraft.data import RefreshMode, default_refresh_plan, run_refresh_plan


def test_default_refresh_plan_verifies_baseline_manifest() -> None:
    results = run_refresh_plan(default_refresh_plan())

    assert len(results) == 1
    assert results[0].dataset_name == "baseline_players"
    assert results[0].mode == RefreshMode.LOCAL_VERIFY
    assert results[0].ok


def test_data_refresh_script_outputs_json() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/data_refresh.py", "--json"],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "."},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "baseline_players" in result.stdout

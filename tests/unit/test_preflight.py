import os
import subprocess
import sys
from pathlib import Path

from bayesiandraft.hardening import PreflightStatus, run_preflight_checks


def test_preflight_passes_core_local_checks() -> None:
    report = run_preflight_checks()

    statuses = {check.name: check.status for check in report.checks}
    assert statuses["league_config"] == PreflightStatus.PASS
    assert statuses["player_snapshot"] == PreflightStatus.PASS
    assert statuses["ingestion_manifest"] == PreflightStatus.PASS
    assert statuses["save_dir"] == PreflightStatus.PASS
    assert statuses["espn_credentials"] == PreflightStatus.WARN
    assert not report.is_blocked


def test_preflight_fails_missing_save_dir(tmp_path: Path) -> None:
    report = run_preflight_checks(save_dir=tmp_path / "missing")

    assert report.is_blocked
    assert any(
        check.name == "save_dir" and check.status == PreflightStatus.FAIL
        for check in report.checks
    )


def test_preflight_script_outputs_json() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/preflight.py", "--json"],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "."},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "league_config" in result.stdout

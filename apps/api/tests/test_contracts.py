import json
import os
import subprocess
import sys
from pathlib import Path

from bayesiandraft_api.contracts import openapi_schema
from bayesiandraft_api.main import create_app


def test_openapi_schema_includes_draft_contracts() -> None:
    schema = openapi_schema(create_app())
    paths = schema["paths"]

    assert "/drafts/{draft_id}/recommendations" in paths
    assert "/drafts/{draft_id}/recommendations/by-position" in paths
    assert "/drafts/{draft_id}/candidate-rollouts" in paths
    assert "/drafts/{draft_id}/picks" in paths


def test_export_openapi_script_writes_schema(tmp_path: Path) -> None:
    output_path = tmp_path / "openapi.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_openapi.py",
            "--out",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": ".:apps/api/src"},
        text=True,
    )

    assert result.returncode == 0, result.stderr
    schema = json.loads(output_path.read_text(encoding="utf-8"))
    assert schema["info"]["title"] == "BayesianDraft API"

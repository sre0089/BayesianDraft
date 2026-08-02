import json
from pathlib import Path

import pytest

from bayesiandraft.data import SnapshotLoadError, load_player_snapshot

FIXTURE_PATH = Path("data/fixtures/baseline_players_2026.json")


def test_loads_baseline_player_snapshot() -> None:
    snapshot = load_player_snapshot(FIXTURE_PATH)

    assert snapshot.snapshot.snapshot_id == "synthetic_players_2026_v1"
    assert snapshot.snapshot.row_count == 12
    assert len(snapshot.players) == 12
    assert len(snapshot.projections) == 12
    assert len(snapshot.adp) == 12
    assert snapshot.players[0].full_name.startswith("Example")


def test_snapshot_rejects_unknown_projection_player(tmp_path: Path) -> None:
    raw_snapshot = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw_snapshot["projections"][0]["player_id"] = "missing_player"
    snapshot_path = tmp_path / "bad_snapshot.json"
    snapshot_path.write_text(json.dumps(raw_snapshot), encoding="utf-8")

    with pytest.raises(SnapshotLoadError, match="Invalid player snapshot"):
        load_player_snapshot(snapshot_path)


def test_snapshot_rejects_wrong_row_count(tmp_path: Path) -> None:
    raw_snapshot = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw_snapshot["snapshot"]["row_count"] = 999
    snapshot_path = tmp_path / "bad_snapshot.json"
    snapshot_path.write_text(json.dumps(raw_snapshot), encoding="utf-8")

    with pytest.raises(SnapshotLoadError, match="Invalid player snapshot"):
        load_player_snapshot(snapshot_path)


def test_snapshot_rejects_wrong_snapshot_reference(tmp_path: Path) -> None:
    raw_snapshot = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw_snapshot["adp"][0]["snapshot_id"] = "other_snapshot"
    snapshot_path = tmp_path / "bad_snapshot.json"
    snapshot_path.write_text(json.dumps(raw_snapshot), encoding="utf-8")

    with pytest.raises(SnapshotLoadError, match="Invalid player snapshot"):
        load_player_snapshot(snapshot_path)

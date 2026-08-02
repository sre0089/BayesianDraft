import csv
import json
from pathlib import Path

from bayesiandraft.data import load_player_snapshot
from bayesiandraft.rankings import (
    RankingConfig,
    build_baseline_rankings,
    export_rankings_csv,
    export_rankings_json,
)

FIXTURE_PATH = Path("data/fixtures/baseline_players_2026.json")


def test_baseline_rankings_are_deterministic() -> None:
    snapshot = load_player_snapshot(FIXTURE_PATH)

    first = build_baseline_rankings(snapshot)
    second = build_baseline_rankings(snapshot)

    assert first == second
    assert [row.overall_rank for row in first] == list(range(1, len(first) + 1))


def test_baseline_rankings_include_position_rank_and_value_metrics() -> None:
    snapshot = load_player_snapshot(FIXTURE_PATH)

    rankings = build_baseline_rankings(snapshot)
    rb_one = next(row for row in rankings if row.player_id == "rb_001")

    assert rb_one.position_rank == 1
    assert rb_one.projected_points == 285
    assert rb_one.vorp > 0
    assert rb_one.value_above_starter >= 0


def test_adp_delta_drives_sleeper_and_fade_scores() -> None:
    snapshot = load_player_snapshot(FIXTURE_PATH)

    rankings = build_baseline_rankings(snapshot, RankingConfig(adp_value_scale=10))
    qb_one = next(row for row in rankings if row.player_id == "qb_001")
    rb_one = next(row for row in rankings if row.player_id == "rb_001")

    assert qb_one.sleeper_score > 0
    assert qb_one.fade_score == 0
    assert rb_one.fade_score >= 0


def test_tiers_break_on_configured_projection_gap() -> None:
    snapshot = load_player_snapshot(FIXTURE_PATH)

    rankings = build_baseline_rankings(snapshot, RankingConfig(tier_gap_points=20))
    rb_tiers = {
        row.player_id: row.tier for row in rankings if row.player_id.startswith("rb_")
    }

    assert rb_tiers["rb_001"] == 1
    assert rb_tiers["rb_002"] == 2
    assert rb_tiers["rb_003"] == 3


def test_rankings_export_json_and_csv(tmp_path: Path) -> None:
    snapshot = load_player_snapshot(FIXTURE_PATH)
    rankings = build_baseline_rankings(snapshot)
    json_path = tmp_path / "rankings.json"
    csv_path = tmp_path / "rankings.csv"

    export_rankings_json(rankings, json_path)
    export_rankings_csv(rankings, csv_path)

    json_rows = json.loads(json_path.read_text(encoding="utf-8"))
    with csv_path.open(encoding="utf-8", newline="") as file:
        csv_rows = list(csv.DictReader(file))

    assert len(json_rows) == len(rankings)
    assert len(csv_rows) == len(rankings)
    assert json_rows[0]["overall_rank"] == 1

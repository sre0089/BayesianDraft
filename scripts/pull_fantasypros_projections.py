import argparse
import csv
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from bayesiandraft.config import load_league_config
from bayesiandraft.data import (
    SnapshotImportError,
    SnapshotImportOptions,
    build_ingestion_manifest_entry,
    import_player_snapshot_csv,
    import_stat_projection_csv,
    write_ingestion_manifest,
    write_player_snapshot,
)

BASE_URL = "https://api.fantasypros.com/public/v2/json/nfl"
DEFAULT_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DST")
CSV_FIELDS = (
    "player_id",
    "full_name",
    "position",
    "team",
    "projected_points",
    "passing_yards",
    "passing_touchdowns",
    "interceptions_thrown",
    "passing_two_point_conversions",
    "rushing_yards",
    "rushing_touchdowns",
    "rushing_two_point_conversions",
    "receiving_yards",
    "receptions",
    "receiving_touchdowns",
    "receiving_two_point_conversions",
    "pat_made",
    "field_goal_missed",
    "fg_made_0_39",
    "fg_made_40_49",
    "fg_made_50_59",
    "fg_made_60_plus",
    "dst_touchdowns",
    "dst_sacks",
    "dst_interceptions",
    "dst_fumble_recoveries",
    "dst_safeties",
    "dst_blocked_kicks",
)

STAT_MAP = {
    "pass_yds": "passing_yards",
    "pass_tds": "passing_touchdowns",
    "pass_ints": "interceptions_thrown",
    "rush_yds": "rushing_yards",
    "rush_tds": "rushing_touchdowns",
    "rec_yds": "receiving_yards",
    "rec_rec": "receptions",
    "rec_tds": "receiving_touchdowns",
    "def_td": "dst_touchdowns",
    "def_sack": "dst_sacks",
    "def_int": "dst_interceptions",
    "def_fr": "dst_fumble_recoveries",
    "def_safety": "dst_safeties",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pull FantasyPros NFL projections into a local BayesianDraft snapshot."
    )
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", type=int, default=0)
    parser.add_argument("--scoring", choices=("PPR", "HALF", "STD"), default="PPR")
    parser.add_argument("--positions", default=",".join(DEFAULT_POSITIONS))
    parser.add_argument("--api-key-env", default="FANTASYPROS_API_KEY")
    parser.add_argument("--raw-out", default="data/raw/fantasypros_projections_2026.json")
    parser.add_argument("--csv-out", default="data/processed/fantasypros_projections_2026.csv")
    parser.add_argument("--out", default="data/processed/fantasypros_projections_2026.json")
    parser.add_argument(
        "--manifest-out",
        default="data/processed/fantasypros_projections_2026.manifest.json",
    )
    parser.add_argument("--snapshot-id", default="fantasypros_projections_2026_latest")
    parser.add_argument("--league-config", default="configs/leagues/espn_2026.yaml")
    parser.add_argument(
        "--score-stats",
        action="store_true",
        help="Recompute fantasy points from normalized stat columns instead of source points.",
    )
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"Set {args.api_key_env} to a FantasyPros API key.")

    raw_path = Path(args.raw_out)
    csv_path = Path(args.csv_out)
    output_path = Path(args.out)
    manifest_path = Path(args.manifest_out)
    positions = tuple(position.strip().upper() for position in args.positions.split(","))
    retrieved_at = datetime.now(UTC)

    try:
        raw_payloads = {
            position: _fetch_position(
                season=args.season,
                week=args.week,
                scoring=args.scoring,
                position=position,
                api_key=api_key,
            )
            for position in positions
            if position
        }
        _write_json(raw_payloads, raw_path)
        rows = _normalized_rows(raw_payloads, scoring=args.scoring)
        _write_csv(rows, csv_path)

        options = SnapshotImportOptions(
            snapshot_id=args.snapshot_id,
            season=args.season,
            source="FantasyPros projections",
            retrieval_timestamp=retrieved_at,
            dataset_name="fantasypros_projections",
            preprocessing_version=(
                "fantasypros_stat_scored_v1" if args.score_stats else "fantasypros_points_v1"
            ),
            license_notes=(
                "FantasyPros API projection data. Keep local unless your API license permits "
                "redistribution."
            ),
            source_url=BASE_URL,
        )
        if args.score_stats:
            snapshot = import_stat_projection_csv(
                csv_path,
                options=options,
                processed_path=output_path,
                league_config=load_league_config(args.league_config),
            )
        else:
            snapshot = import_player_snapshot_csv(
                csv_path,
                options=options,
                processed_path=output_path,
            )
        write_player_snapshot(snapshot, output_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        write_ingestion_manifest(
            build_ingestion_manifest_entry(
                snapshot_id=snapshot.snapshot.snapshot_id,
                dataset_name=snapshot.snapshot.dataset_name,
                source=snapshot.snapshot.source,
                retrieval_timestamp=snapshot.snapshot.retrieval_timestamp,
                season=snapshot.snapshot.season,
                processed_path=output_path,
                schema_version=snapshot.snapshot.schema_version,
                preprocessing_version=snapshot.snapshot.preprocessing_version,
                license_notes=snapshot.snapshot.license_notes,
                row_count=snapshot.snapshot.row_count,
                source_url=snapshot.snapshot.source_url,
                raw_path=raw_path,
            ),
            manifest_path,
        )
    except (OSError, SnapshotImportError, URLError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Wrote {snapshot.snapshot.row_count} players to {output_path}")
    print(f"Normalized CSV: {csv_path}")
    print(f"Raw JSON: {raw_path}")
    print(f"Manifest: {manifest_path}")


def _fetch_position(
    *,
    season: int,
    week: int,
    scoring: str,
    position: str,
    api_key: str,
) -> dict[str, Any]:
    query = urlencode({"position": position, "week": week, "scoring": scoring})
    request = Request(
        f"{BASE_URL}/{season}/projections?{query}",
        headers={"x-api-key": api_key},
    )
    with urlopen(request, timeout=30) as response:
        return cast(dict[str, Any], json.loads(response.read().decode("utf-8")))


def _normalized_rows(
    raw_payloads: dict[str, dict[str, Any]],
    *,
    scoring: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for payload in raw_payloads.values():
        for player in payload.get("players", []):
            row = _normalized_player_row(player, scoring=scoring)
            player_id = row["player_id"]
            if not player_id or player_id in seen_ids:
                continue
            seen_ids.add(player_id)
            rows.append(row)
    return rows


def _normalized_player_row(player: dict[str, Any], *, scoring: str) -> dict[str, str]:
    stats = _stats_dict(player.get("stats"))
    row = {field: "" for field in CSV_FIELDS}
    row["player_id"] = f"fp_{player.get('fpid') or player.get('player_id')}"
    row["full_name"] = str(player.get("name") or "")
    row["position"] = str(player.get("position_id") or "")
    row["team"] = str(player.get("team_id") or "")
    row["projected_points"] = _source_points(stats, scoring=scoring)
    for source_key, target_key in STAT_MAP.items():
        if source_key in stats and stats[source_key] is not None:
            row[target_key] = str(stats[source_key])
    return row


def _stats_dict(raw_stats: Any) -> dict[str, Any]:
    if isinstance(raw_stats, list):
        if not raw_stats:
            return {}
        raw_stats = raw_stats[0]
    return raw_stats if isinstance(raw_stats, dict) else {}


def _source_points(stats: dict[str, Any], *, scoring: str) -> str:
    keys = {
        "PPR": ("points_ppr", "points"),
        "HALF": ("points_half", "points"),
        "STD": ("points",),
    }[scoring]
    for key in keys:
        value = stats.get(key)
        if value is not None:
            return str(value)
    return ""


def _write_json(payload: dict[str, dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

import argparse
from datetime import UTC, datetime
from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import (
    SnapshotImportError,
    SnapshotImportOptions,
    build_ingestion_manifest_entry,
    default_snapshot_id,
    import_player_snapshot_csv,
    import_stat_projection_csv,
    write_ingestion_manifest,
    write_player_snapshot,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a local player projection CSV into a BayesianDraft snapshot."
    )
    parser.add_argument("--players", required=True, help="Path to the local projection CSV.")
    parser.add_argument("--out", required=True, help="Path for the processed snapshot JSON.")
    parser.add_argument("--manifest-out", help="Optional path for the ingestion manifest JSON.")
    parser.add_argument(
        "--mode",
        choices=("points", "stats"),
        default="points",
        help=(
            "Import mode. 'points' expects projected_points; 'stats' scores stat-line columns "
            "with the configured league rules."
        ),
    )
    parser.add_argument(
        "--league-config",
        default="configs/leagues/espn_2026.yaml",
        help="League scoring config used by --mode stats.",
    )
    parser.add_argument("--snapshot-id", help="Snapshot ID. Defaults to a source/season timestamp.")
    parser.add_argument("--season", required=True, type=int, help="NFL season for the snapshot.")
    parser.add_argument("--source", required=True, help="Human-readable source name.")
    parser.add_argument("--source-url", help="Optional source URL.")
    parser.add_argument(
        "--dataset-name",
        default="imported_players",
        help="Dataset name stored in snapshot metadata.",
    )
    parser.add_argument(
        "--license-notes",
        default="User-provided local projection file. Do not redistribute without permission.",
        help="License or redistribution notes stored in metadata.",
    )
    parser.add_argument(
        "--retrieved-at",
        help="ISO-8601 retrieval timestamp. Defaults to the current UTC time.",
    )
    args = parser.parse_args()

    retrieved_at = _parse_retrieved_at(args.retrieved_at)
    snapshot_id = args.snapshot_id or default_snapshot_id(args.season, args.source, retrieved_at)
    output_path = Path(args.out)
    options = SnapshotImportOptions(
        snapshot_id=snapshot_id,
        season=args.season,
        source=args.source,
        retrieval_timestamp=retrieved_at,
        dataset_name=args.dataset_name,
        license_notes=args.license_notes,
        source_url=args.source_url,
    )

    try:
        if args.mode == "stats":
            snapshot = import_stat_projection_csv(
                args.players,
                options=options,
                processed_path=output_path,
                league_config=load_league_config(args.league_config),
            )
        else:
            snapshot = import_player_snapshot_csv(
                args.players,
                options=options,
                processed_path=output_path,
            )
        write_player_snapshot(snapshot, output_path)

        if args.manifest_out:
            Path(args.manifest_out).parent.mkdir(parents=True, exist_ok=True)
            manifest = build_ingestion_manifest_entry(
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
                raw_path=args.players,
            )
            write_ingestion_manifest(manifest, args.manifest_out)
    except SnapshotImportError as exc:
        raise SystemExit(str(exc)) from exc

    print(snapshot.model_dump_json(indent=2, exclude_none=True))


def _parse_retrieved_at(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)

    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


if __name__ == "__main__":
    main()

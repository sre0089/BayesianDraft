import argparse
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from bayesiandraft.data import (
    SnapshotImportError,
    SnapshotImportOptions,
    build_ingestion_manifest_entry,
    import_dynastyprocess_rankings_csv,
    write_ingestion_manifest,
    write_player_snapshot,
)

DEFAULT_SOURCE_URL = (
    "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_fpecr_latest.csv"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pull public DynastyProcess/FantasyPros ECR rankings into a snapshot."
    )
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--raw-out", default="data/raw/dynastyprocess_db_fpecr_latest.csv")
    parser.add_argument("--out", default="data/processed/dynastyprocess_rankings_2026.json")
    parser.add_argument(
        "--manifest-out",
        default="data/processed/dynastyprocess_rankings_2026.manifest.json",
    )
    parser.add_argument("--snapshot-id", default="dynastyprocess_rankings_2026_latest")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--page-type", default="redraft-overall")
    args = parser.parse_args()

    raw_path = Path(args.raw_out)
    output_path = Path(args.out)
    manifest_path = Path(args.manifest_out)
    retrieved_at = datetime.now(UTC)

    try:
        _download(args.source_url, raw_path)
        snapshot = import_dynastyprocess_rankings_csv(
            raw_path,
            options=SnapshotImportOptions(
                snapshot_id=args.snapshot_id,
                season=args.season,
                source="DynastyProcess FantasyPros ECR",
                retrieval_timestamp=retrieved_at,
                dataset_name="dynastyprocess_rankings",
                preprocessing_version="dynastyprocess_ecr_proxy_v1",
                license_notes=(
                    "Public DynastyProcess data with FantasyPros ECR rankings. "
                    "Projection fields are rank-derived proxies, not independent stat projections."
                ),
                source_url=args.source_url,
            ),
            processed_path=output_path,
            page_type=args.page_type,
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

    print(
        f"Wrote {snapshot.snapshot.row_count} players to {output_path} "
        f"from {snapshot.snapshot.source_url}"
    )
    print(f"Raw CSV: {raw_path}")
    print(f"Manifest: {manifest_path}")


def _download(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=30) as response:
        output_path.write_bytes(response.read())


if __name__ == "__main__":
    main()

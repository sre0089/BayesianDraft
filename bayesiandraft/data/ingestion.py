import hashlib
import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, NonNegativeInt, ValidationError


class IngestionManifestError(ValueError):
    """Raised when an ingestion manifest cannot be loaded or verified."""


class IngestionManifestEntry(BaseModel):
    snapshot_id: str
    dataset_name: str
    source: str
    retrieval_timestamp: datetime
    season: int
    checksum: str
    processed_path: str
    schema_version: str
    preprocessing_version: str
    license_notes: str
    row_count: NonNegativeInt
    source_url: str | None = None
    raw_path: str | None = None


def sha256_file(path: str | Path) -> str:
    file_path = Path(path)
    digest = hashlib.sha256()
    try:
        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise IngestionManifestError(f"Unable to hash file: {file_path}") from exc
    return digest.hexdigest()


def load_ingestion_manifest(path: str | Path) -> IngestionManifestEntry:
    manifest_path = Path(path)
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise IngestionManifestError(f"Unable to read ingestion manifest: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        message = f"Invalid JSON in ingestion manifest: {manifest_path}"
        raise IngestionManifestError(message) from exc

    try:
        return IngestionManifestEntry.model_validate(raw_manifest)
    except ValidationError as exc:
        raise IngestionManifestError(f"Invalid ingestion manifest: {manifest_path}") from exc


def write_ingestion_manifest(entry: IngestionManifestEntry, path: str | Path) -> None:
    manifest_path = Path(path)
    manifest_path.write_text(
        entry.model_dump_json(indent=2, exclude_none=True) + "\n",
        encoding="utf-8",
    )


def build_ingestion_manifest_entry(
    *,
    snapshot_id: str,
    dataset_name: str,
    source: str,
    retrieval_timestamp: datetime,
    season: int,
    processed_path: str | Path,
    schema_version: str,
    preprocessing_version: str,
    license_notes: str,
    row_count: int,
    source_url: str | None = None,
    raw_path: str | Path | None = None,
) -> IngestionManifestEntry:
    return IngestionManifestEntry(
        snapshot_id=snapshot_id,
        dataset_name=dataset_name,
        source=source,
        retrieval_timestamp=retrieval_timestamp,
        season=season,
        checksum=sha256_file(processed_path),
        processed_path=str(processed_path),
        schema_version=schema_version,
        preprocessing_version=preprocessing_version,
        license_notes=license_notes,
        row_count=row_count,
        source_url=source_url,
        raw_path=None if raw_path is None else str(raw_path),
    )


def verify_ingestion_manifest(
    entry: IngestionManifestEntry,
    *,
    root: str | Path = ".",
) -> bool:
    root_path = Path(root)
    processed_path = root_path / entry.processed_path
    if not processed_path.exists():
        raise IngestionManifestError(f"Processed file is missing: {entry.processed_path}")

    actual_checksum = sha256_file(processed_path)
    if actual_checksum != entry.checksum:
        raise IngestionManifestError(
            f"Checksum mismatch for {entry.processed_path}: "
            f"expected {entry.checksum}, got {actual_checksum}"
        )

    if entry.raw_path is not None and not (root_path / entry.raw_path).exists():
        raise IngestionManifestError(f"Raw file is missing: {entry.raw_path}")

    return True

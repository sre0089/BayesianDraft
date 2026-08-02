from datetime import UTC, datetime

import pytest

from bayesiandraft.data import (
    IngestionManifestError,
    build_ingestion_manifest_entry,
    load_ingestion_manifest,
    verify_ingestion_manifest,
    write_ingestion_manifest,
)


def test_builds_writes_and_loads_manifest(tmp_path) -> None:
    processed_path = tmp_path / "processed.json"
    processed_path.write_text('{"ok": true}\n', encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"

    entry = build_ingestion_manifest_entry(
        snapshot_id="fixture_v1",
        dataset_name="fixture",
        source="synthetic",
        retrieval_timestamp=datetime(2026, 8, 2, tzinfo=UTC),
        season=2026,
        processed_path=processed_path,
        schema_version="1",
        preprocessing_version="manual_v1",
        license_notes="Synthetic fixture.",
        row_count=1,
    )

    write_ingestion_manifest(entry, manifest_path)

    assert load_ingestion_manifest(manifest_path) == entry
    assert verify_ingestion_manifest(entry)


def test_verify_manifest_rejects_checksum_mismatch(tmp_path) -> None:
    processed_path = tmp_path / "processed.json"
    processed_path.write_text('{"ok": true}\n', encoding="utf-8")
    entry = build_ingestion_manifest_entry(
        snapshot_id="fixture_v1",
        dataset_name="fixture",
        source="synthetic",
        retrieval_timestamp=datetime(2026, 8, 2, tzinfo=UTC),
        season=2026,
        processed_path=processed_path,
        schema_version="1",
        preprocessing_version="manual_v1",
        license_notes="Synthetic fixture.",
        row_count=1,
    ).model_copy(update={"checksum": "bad-checksum"})

    with pytest.raises(IngestionManifestError, match="Checksum mismatch"):
        verify_ingestion_manifest(entry)


def test_load_manifest_rejects_invalid_json(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{", encoding="utf-8")

    with pytest.raises(IngestionManifestError, match="Invalid JSON"):
        load_ingestion_manifest(manifest_path)

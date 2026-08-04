import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from bayesiandraft.data.ingestion import sha256_file
from bayesiandraft.data.snapshots import PlayerSnapshot
from bayesiandraft.domain import (
    ADPRecord,
    DataSnapshotRecord,
    PlayerRecord,
    Position,
    ProjectionRecord,
)

REQUIRED_PLAYER_COLUMNS = frozenset(
    {"player_id", "full_name", "position", "projected_points"}
)


class SnapshotImportError(ValueError):
    """Raised when local projection data cannot be imported."""


@dataclass(frozen=True)
class SnapshotImportOptions:
    snapshot_id: str
    season: int
    source: str
    retrieval_timestamp: datetime
    dataset_name: str = "imported_players"
    schema_version: str = "1"
    preprocessing_version: str = "csv_import_v1"
    license_notes: str = (
        "User-provided local projection file. Do not redistribute without permission."
    )
    source_url: str | None = None


def import_player_snapshot_csv(
    csv_path: str | Path,
    *,
    options: SnapshotImportOptions,
    processed_path: str | Path,
) -> PlayerSnapshot:
    input_path = Path(csv_path)
    rows = _read_csv_rows(input_path)
    _validate_required_columns(set(rows[0].keys()), input_path)

    players: list[PlayerRecord] = []
    projections: list[ProjectionRecord] = []
    adp_records: list[ADPRecord] = []

    seen_player_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        player_id = _required_text(row, "player_id", row_number)
        if player_id in seen_player_ids:
            raise SnapshotImportError(f"row {row_number}: duplicate player_id '{player_id}'")
        seen_player_ids.add(player_id)

        players.append(_build_player(row, row_number))
        projections.append(_build_projection(row, row_number, player_id, options))

        adp_record = _build_adp(row, row_number, player_id, options)
        if adp_record is not None:
            adp_records.append(adp_record)

    snapshot = DataSnapshotRecord(
        snapshot_id=options.snapshot_id,
        dataset_name=options.dataset_name,
        source=options.source,
        retrieval_timestamp=options.retrieval_timestamp,
        season=options.season,
        checksum=sha256_file(input_path),
        raw_path=str(input_path),
        processed_path=str(processed_path),
        schema_version=options.schema_version,
        preprocessing_version=options.preprocessing_version,
        license_notes=options.license_notes,
        source_url=options.source_url,
        row_count=len(players),
    )

    try:
        return PlayerSnapshot(
            snapshot=snapshot,
            players=players,
            projections=projections,
            adp=adp_records,
            injuries=[],
        )
    except ValidationError as exc:
        raise SnapshotImportError("imported snapshot failed validation") from exc
    except ValueError as exc:
        raise SnapshotImportError(str(exc)) from exc


def write_player_snapshot(snapshot: PlayerSnapshot, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot.model_dump(mode="json", exclude_none=True), indent=2) + "\n",
        encoding="utf-8",
    )


def default_snapshot_id(season: int, source: str, timestamp: datetime | None = None) -> str:
    stamp = (timestamp or datetime.now(UTC)).strftime("%Y%m%d%H%M%S")
    slug = "".join(character.lower() if character.isalnum() else "_" for character in source)
    slug = "_".join(part for part in slug.split("_") if part)
    return f"{slug or 'local'}_{season}_{stamp}"


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)
    except OSError as exc:
        raise SnapshotImportError(f"unable to read CSV file: {path}") from exc

    if not rows:
        raise SnapshotImportError(f"CSV file has no data rows: {path}")
    return rows


def _validate_required_columns(columns: set[str], path: Path) -> None:
    missing = REQUIRED_PLAYER_COLUMNS - columns
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise SnapshotImportError(f"CSV file is missing required columns: {missing_columns}")


def _build_player(row: dict[str, str], row_number: int) -> PlayerRecord:
    try:
        return PlayerRecord(
            player_id=_required_text(row, "player_id", row_number),
            full_name=_required_text(row, "full_name", row_number),
            first_name=_optional_text(row, "first_name"),
            last_name=_optional_text(row, "last_name"),
            position=Position(_required_text(row, "position", row_number)),
            nfl_team_id=_optional_text(row, "team"),
            status=_optional_text(row, "status") or "active",
            bye_week=_optional_int(row, "bye_week", row_number),
        )
    except ValidationError as exc:
        raise SnapshotImportError(f"row {row_number}: invalid player record") from exc


def _build_projection(
    row: dict[str, str],
    row_number: int,
    player_id: str,
    options: SnapshotImportOptions,
) -> ProjectionRecord:
    mean = _required_float(row, "projected_points", row_number)
    median = _optional_float(row, "median_points", row_number)
    lower = _optional_float(row, "floor_points", row_number)
    upper = _optional_float(row, "ceiling_points", row_number)
    generated_at = options.retrieval_timestamp

    try:
        return ProjectionRecord(
            projection_id=f"proj_{player_id}",
            player_id=player_id,
            season=options.season,
            scope="season",
            mean=mean,
            median=mean if median is None else median,
            lower_quantile=round(mean * 0.8, 4) if lower is None else lower,
            upper_quantile=round(mean * 1.2, 4) if upper is None else upper,
            games_played_mean=_optional_float(row, "games_played", row_number),
            model_version=options.preprocessing_version,
            data_snapshot_id=options.snapshot_id,
            generated_at=generated_at,
        )
    except ValidationError as exc:
        raise SnapshotImportError(f"row {row_number}: invalid projection record") from exc


def _build_adp(
    row: dict[str, str],
    row_number: int,
    player_id: str,
    options: SnapshotImportOptions,
) -> ADPRecord | None:
    overall_adp = _optional_float(row, "overall_adp", row_number)
    if overall_adp is None:
        return None

    try:
        return ADPRecord(
            adp_id=f"adp_{player_id}",
            player_id=player_id,
            source=options.source,
            format="redraft",
            scoring="full_ppr",
            date=options.retrieval_timestamp.date(),
            overall_adp=overall_adp,
            position_adp=_optional_float(row, "position_adp", row_number),
            rank=_optional_int(row, "adp_rank", row_number),
            snapshot_id=options.snapshot_id,
        )
    except ValidationError as exc:
        raise SnapshotImportError(f"row {row_number}: invalid ADP record") from exc


def _required_text(row: dict[str, str], column: str, row_number: int) -> str:
    value = _optional_text(row, column)
    if value is None:
        raise SnapshotImportError(f"row {row_number}: missing required value '{column}'")
    return value


def _optional_text(row: dict[str, str], column: str) -> str | None:
    value = row.get(column)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _required_float(row: dict[str, str], column: str, row_number: int) -> float:
    value = _optional_float(row, column, row_number)
    if value is None:
        raise SnapshotImportError(f"row {row_number}: missing required value '{column}'")
    return value


def _optional_float(row: dict[str, str], column: str, row_number: int) -> float | None:
    value = _optional_text(row, column)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise SnapshotImportError(f"row {row_number}: invalid number for '{column}'") from exc


def _optional_int(row: dict[str, str], column: str, row_number: int) -> int | None:
    value = _optional_text(row, column)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise SnapshotImportError(f"row {row_number}: invalid integer for '{column}'") from exc

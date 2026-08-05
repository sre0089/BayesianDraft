import csv
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
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
SUPPORTED_FANTASY_POSITIONS = frozenset({"QB", "RB", "WR", "TE", "K", "DST"})

POSITION_PROJECTION_TOPS = {
    "QB": 340.0,
    "RB": 300.0,
    "WR": 285.0,
    "TE": 220.0,
    "K": 165.0,
    "DST": 155.0,
}

POSITION_PROJECTION_FLOORS = {
    "QB": 210.0,
    "RB": 90.0,
    "WR": 90.0,
    "TE": 70.0,
    "K": 95.0,
    "DST": 85.0,
}

POSITION_PROJECTION_DECAY = {
    "QB": 2.0,
    "RB": 2.2,
    "WR": 1.8,
    "TE": 1.5,
    "K": 1.0,
    "DST": 1.0,
}


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


def import_dynastyprocess_rankings_csv(
    csv_path: str | Path,
    *,
    options: SnapshotImportOptions,
    processed_path: str | Path,
    page_type: str = "redraft-overall",
) -> PlayerSnapshot:
    input_path = Path(csv_path)
    rows = _read_csv_rows(input_path)
    required_columns = {"player", "id", "pos", "team", "ecr", "bye", "scrape_date"}
    _validate_columns(set(rows[0].keys()), required_columns, input_path)

    filtered_rows = _latest_rankings_rows(rows, page_type=page_type)
    if not filtered_rows:
        raise SnapshotImportError(f"no supported rankings rows found for page_type '{page_type}'")

    positional_ranks = _positional_rank_lookup(filtered_rows)
    players: list[PlayerRecord] = []
    projections: list[ProjectionRecord] = []
    adp_records: list[ADPRecord] = []

    for row_number, row in filtered_rows:
        player_id = f"fp_{_required_text(row, 'id', row_number)}"
        position = _required_text(row, "pos", row_number)
        position_rank = positional_ranks[player_id]
        mean = _projection_proxy(position, position_rank)
        ecr = _required_float(row, "ecr", row_number)

        try:
            players.append(
                PlayerRecord(
                    player_id=player_id,
                    full_name=_required_text(row, "player", row_number),
                    position=Position(position),
                    nfl_team_id=_optional_text(row, "tm") or _optional_text(row, "team"),
                    bye_week=_optional_int(row, "bye", row_number),
                    source_player_ids={"fantasypros": _required_text(row, "id", row_number)},
                )
            )
            projections.append(
                ProjectionRecord(
                    projection_id=f"proj_{player_id}",
                    player_id=player_id,
                    season=options.season,
                    scope="season",
                    mean=mean,
                    median=mean,
                    lower_quantile=round(mean * 0.8, 4),
                    upper_quantile=round(mean * 1.2, 4),
                    games_played_mean=17,
                    model_version=options.preprocessing_version,
                    data_snapshot_id=options.snapshot_id,
                    generated_at=options.retrieval_timestamp,
                )
            )
            adp_records.append(
                ADPRecord(
                    adp_id=f"adp_{player_id}",
                    player_id=player_id,
                    source=options.source,
                    format="redraft",
                    scoring="full_ppr",
                    date=_parse_date(_required_text(row, "scrape_date", row_number), row_number),
                    overall_adp=ecr,
                    position_adp=float(position_rank),
                    rank=round(ecr),
                    snapshot_id=options.snapshot_id,
                )
            )
        except (ValidationError, ValueError) as exc:
            raise SnapshotImportError(f"row {row_number}: invalid rankings record") from exc

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
        raise SnapshotImportError("imported DynastyProcess snapshot failed validation") from exc
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
    _validate_columns(columns, REQUIRED_PLAYER_COLUMNS, path)


def _validate_columns(
    columns: set[str],
    required_columns: frozenset[str] | set[str],
    path: Path,
) -> None:
    missing = required_columns - columns
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
    except (ValidationError, ValueError) as exc:
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
    if stripped.upper() in {"NA", "N/A", "NULL", "NONE"}:
        return None
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


def _latest_rankings_rows(
    rows: list[dict[str, str]],
    *,
    page_type: str,
) -> list[tuple[int, dict[str, str]]]:
    candidates = [
        (row_number, row)
        for row_number, row in enumerate(rows, start=2)
        if row.get("page_type") == page_type
        and row.get("pos") in SUPPORTED_FANTASY_POSITIONS
        and _optional_text(row, "ecr") is not None
    ]
    if not candidates:
        return []

    latest_scrape_date = max(
        _required_text(row, "scrape_date", row_number) for row_number, row in candidates
    )
    latest_rows = [
        (row_number, row)
        for row_number, row in candidates
        if _required_text(row, "scrape_date", row_number) == latest_scrape_date
    ]
    latest_rows.sort(key=lambda item: _required_float(item[1], "ecr", item[0]))

    deduped: dict[str, tuple[int, dict[str, str]]] = {}
    for row_number, row in latest_rows:
        player_id = _required_text(row, "id", row_number)
        deduped.setdefault(player_id, (row_number, row))
    return list(deduped.values())


def _positional_rank_lookup(rows: list[tuple[int, dict[str, str]]]) -> dict[str, int]:
    by_position: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for row_number, row in rows:
        by_position.setdefault(_required_text(row, "pos", row_number), []).append((row_number, row))

    lookup: dict[str, int] = {}
    for position_rows in by_position.values():
        position_rows.sort(key=lambda item: _required_float(item[1], "ecr", item[0]))
        for rank, (row_number, row) in enumerate(position_rows, start=1):
            lookup[f"fp_{_required_text(row, 'id', row_number)}"] = rank
    return lookup


def _projection_proxy(position: str, position_rank: int) -> float:
    top = POSITION_PROJECTION_TOPS[position]
    floor = POSITION_PROJECTION_FLOORS[position]
    decay = POSITION_PROJECTION_DECAY[position]
    return round(max(floor, top - ((position_rank - 1) * decay)), 4)


def _parse_date(value: str, row_number: int) -> date:
    try:
        return datetime.fromisoformat(value).date()
    except ValueError as exc:
        raise SnapshotImportError(f"row {row_number}: invalid date") from exc

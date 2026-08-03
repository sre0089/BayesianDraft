from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from bayesiandraft.config import LeagueConfigError, load_league_config
from bayesiandraft.data import (
    IngestionManifestError,
    load_ingestion_manifest,
    load_player_snapshot,
    verify_ingestion_manifest,
)
from bayesiandraft.data.snapshots import SnapshotLoadError
from bayesiandraft.integrations.espn import EspnCredentialStatus, load_espn_config_from_env


class PreflightStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class PreflightCheck(BaseModel):
    name: str
    status: PreflightStatus
    message: str


class PreflightReport(BaseModel):
    checks: list[PreflightCheck]

    @property
    def is_blocked(self) -> bool:
        return any(check.status == PreflightStatus.FAIL for check in self.checks)


def run_preflight_checks(
    *,
    league_config_path: str | Path = "configs/leagues/espn_2026.yaml",
    player_snapshot_path: str | Path = "data/fixtures/baseline_players_2026.json",
    manifest_path: str | Path = "data/manifests/baseline_players_2026.json",
    save_dir: str | Path = "data/snapshots",
) -> PreflightReport:
    checks = [
        _check_league_config(league_config_path),
        _check_player_snapshot(player_snapshot_path),
        _check_manifest(manifest_path),
        _check_save_dir(save_dir),
    ]
    checks.append(_check_espn_credentials())
    return PreflightReport(checks=checks)


def _check_league_config(path: str | Path) -> PreflightCheck:
    try:
        load_league_config(path)
    except LeagueConfigError as exc:
        return PreflightCheck(
            name="league_config",
            status=PreflightStatus.FAIL,
            message=str(exc),
        )
    return PreflightCheck(
        name="league_config",
        status=PreflightStatus.PASS,
        message="League config loads and validates.",
    )


def _check_player_snapshot(path: str | Path) -> PreflightCheck:
    try:
        load_player_snapshot(path)
    except SnapshotLoadError as exc:
        return PreflightCheck(
            name="player_snapshot",
            status=PreflightStatus.FAIL,
            message=str(exc),
        )
    return PreflightCheck(
        name="player_snapshot",
        status=PreflightStatus.PASS,
        message="Player snapshot loads and validates.",
    )


def _check_manifest(path: str | Path) -> PreflightCheck:
    try:
        manifest = load_ingestion_manifest(path)
        verify_ingestion_manifest(manifest)
    except IngestionManifestError as exc:
        return PreflightCheck(
            name="ingestion_manifest",
            status=PreflightStatus.FAIL,
            message=str(exc),
        )
    return PreflightCheck(
        name="ingestion_manifest",
        status=PreflightStatus.PASS,
        message="Ingestion manifest checksum validates.",
    )


def _check_save_dir(path: str | Path) -> PreflightCheck:
    save_path = Path(path)
    if not save_path.exists():
        return PreflightCheck(
            name="save_dir",
            status=PreflightStatus.FAIL,
            message=f"Save directory does not exist: {save_path}",
        )
    if not save_path.is_dir():
        return PreflightCheck(
            name="save_dir",
            status=PreflightStatus.FAIL,
            message=f"Save path is not a directory: {save_path}",
        )
    return PreflightCheck(
        name="save_dir",
        status=PreflightStatus.PASS,
        message="Save directory exists.",
    )


def _check_espn_credentials() -> PreflightCheck:
    config = load_espn_config_from_env(season=2026)
    if config.credential_status == EspnCredentialStatus.CONFIGURED:
        return PreflightCheck(
            name="espn_credentials",
            status=PreflightStatus.PASS,
            message="ESPN credentials are configured.",
        )
    return PreflightCheck(
        name="espn_credentials",
        status=PreflightStatus.WARN,
        message="ESPN credentials are missing; manual draft mode remains available.",
    )

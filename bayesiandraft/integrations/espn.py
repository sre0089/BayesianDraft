import os
from enum import StrEnum

from pydantic import BaseModel, Field, PositiveInt


class EspnCredentialStatus(StrEnum):
    CONFIGURED = "configured"
    MISSING = "missing"


class EspnSyncStatus(StrEnum):
    READY = "ready"
    SKIPPED = "skipped"
    FAILED = "failed"


class EspnIntegrationConfig(BaseModel):
    league_id: str | None = None
    season: PositiveInt
    swid: str | None = Field(default=None, repr=False)
    espn_s2: str | None = Field(default=None, repr=False)

    @property
    def credential_status(self) -> EspnCredentialStatus:
        if self.league_id and self.swid and self.espn_s2:
            return EspnCredentialStatus.CONFIGURED
        return EspnCredentialStatus.MISSING


class EspnDraftPick(BaseModel):
    overall_pick: int
    manager_id: str
    player_id: str
    raw_player_name: str | None = None


class EspnSyncResult(BaseModel):
    status: EspnSyncStatus
    credential_status: EspnCredentialStatus
    imported_picks: list[EspnDraftPick] = Field(default_factory=list)
    message: str


def load_espn_config_from_env(*, season: int) -> EspnIntegrationConfig:
    return EspnIntegrationConfig(
        league_id=os.getenv("ESPN_LEAGUE_ID"),
        season=season,
        swid=os.getenv("ESPN_SWID"),
        espn_s2=os.getenv("ESPN_S2"),
    )


def dry_run_sync(config: EspnIntegrationConfig) -> EspnSyncResult:
    if config.credential_status == EspnCredentialStatus.MISSING:
        return EspnSyncResult(
            status=EspnSyncStatus.SKIPPED,
            credential_status=config.credential_status,
            message="ESPN credentials are not configured.",
        )

    return EspnSyncResult(
        status=EspnSyncStatus.READY,
        credential_status=config.credential_status,
        message="ESPN credentials are configured; live sync is intentionally disabled.",
    )

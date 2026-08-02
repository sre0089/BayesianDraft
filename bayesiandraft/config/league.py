from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, PositiveInt, ValidationError, field_validator


class DraftManagerConfig(BaseModel):
    id: str
    name: str


class LeagueMetadata(BaseModel):
    format: str
    team_count: PositiveInt
    draft_type: str
    scoring_format: str
    trades_enabled: bool
    waiver_rules: str
    draft_date: date
    user_manager_id: str
    user_draft_position: PositiveInt


class RosterConfig(BaseModel):
    starting_slots: dict[str, int]
    bench_slots: int
    ir_slots: int
    flex_eligibility: dict[str, list[str]]


class RangeScoringBucket(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    min_value: int = Field(alias="min")
    max_value: int | None = Field(alias="max")
    points: float

    def contains(self, value: int) -> bool:
        if value < self.min_value:
            return False
        return self.max_value is None or value <= self.max_value


class FieldGoalBucket(BaseModel):
    min_yards: int
    max_yards: int | None
    points: float

    def contains(self, yards: int) -> bool:
        if yards < self.min_yards:
            return False
        return self.max_yards is None or yards <= self.max_yards


class PassingScoringConfig(BaseModel):
    yards: float
    touchdown: float
    interception: float
    two_point_conversion: float


class RushingScoringConfig(BaseModel):
    yards: float
    touchdown: float
    two_point_conversion: float


class ReceivingScoringConfig(BaseModel):
    yards: float
    reception: float
    touchdown: float
    two_point_conversion: float


class KickingScoringConfig(BaseModel):
    pat_made: float
    field_goal_missed: float
    field_goal_made: list[FieldGoalBucket]


class DefenseSpecialTeamsScoringConfig(BaseModel):
    touchdowns: dict[str, float]
    returns: dict[str, float]
    events: dict[str, float]
    points_allowed: list[RangeScoringBucket]
    yards_allowed: list[RangeScoringBucket]


class ScoringConfig(BaseModel):
    passing: PassingScoringConfig
    rushing: RushingScoringConfig
    receiving: ReceivingScoringConfig
    kicking: KickingScoringConfig
    defense_special_teams: DefenseSpecialTeamsScoringConfig


class LeagueConfig(BaseModel):
    platform: str
    season: int
    league: LeagueMetadata
    draft_order: list[DraftManagerConfig]
    roster: RosterConfig
    scoring: ScoringConfig

    @field_validator("draft_order")
    @classmethod
    def draft_order_must_have_unique_manager_ids(
        cls, draft_order: list[DraftManagerConfig]
    ) -> list[DraftManagerConfig]:
        manager_ids = [manager.id for manager in draft_order]
        if len(manager_ids) != len(set(manager_ids)):
            raise ValueError("draft_order manager ids must be unique")
        return draft_order

    @field_validator("draft_order")
    @classmethod
    def draft_order_must_not_be_empty(
        cls, draft_order: list[DraftManagerConfig]
    ) -> list[DraftManagerConfig]:
        if not draft_order:
            raise ValueError("draft_order must not be empty")
        return draft_order

    def model_post_init(self, __context: Any) -> None:
        if self.league.team_count != len(self.draft_order):
            raise ValueError("league.team_count must equal draft_order length")

        manager_ids = {manager.id for manager in self.draft_order}
        if self.league.user_manager_id not in manager_ids:
            raise ValueError("league.user_manager_id must exist in draft_order")

        if self.league.user_draft_position > self.league.team_count:
            raise ValueError("league.user_draft_position cannot exceed league.team_count")

        user_slot = self.draft_order[self.league.user_draft_position - 1]
        if user_slot.id != self.league.user_manager_id:
            raise ValueError("league.user_draft_position must match league.user_manager_id")


class LeagueConfigError(ValueError):
    """Raised when a league config file cannot be loaded or validated."""


def load_league_config(path: str | Path) -> LeagueConfig:
    config_path = Path(path)
    try:
        raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise LeagueConfigError(f"Unable to read league config: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise LeagueConfigError(f"Invalid YAML in league config: {config_path}") from exc

    if not isinstance(raw_config, dict):
        raise LeagueConfigError("League config must be a YAML mapping")

    try:
        return LeagueConfig.model_validate(raw_config)
    except ValidationError as exc:
        raise LeagueConfigError(f"Invalid league config: {config_path}") from exc

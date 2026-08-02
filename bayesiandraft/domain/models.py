from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveInt,
    field_validator,
)


class Position(StrEnum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DST = "DST"


class GameType(StrEnum):
    REGULAR = "REG"
    POSTSEASON = "POST"


class SourceMetadata(BaseModel):
    source: str
    source_url: str | None = None
    source_snapshot_id: str
    retrieved_at: datetime


class PlayerRecord(BaseModel):
    player_id: str
    full_name: str
    first_name: str | None = None
    last_name: str | None = None
    position: Position
    nfl_team_id: str | None = None
    status: str = "active"
    age: NonNegativeFloat | None = None
    height: str | None = None
    weight: NonNegativeInt | None = None
    experience: NonNegativeInt | None = None
    rookie: bool = False
    draft_year: int | None = None
    draft_round: NonNegativeInt | None = None
    draft_pick: NonNegativeInt | None = None
    bye_week: int | None = None
    source_player_ids: dict[str, str] = Field(default_factory=dict)
    valid_from: date | None = None
    valid_to: date | None = None

    @field_validator("bye_week")
    @classmethod
    def bye_week_must_be_in_nfl_range(cls, bye_week: int | None) -> int | None:
        if bye_week is not None and not 1 <= bye_week <= 18:
            raise ValueError("bye_week must be between 1 and 18")
        return bye_week


class TeamRecord(BaseModel):
    team_id: str
    abbreviation: str
    full_name: str
    conference: str | None = None
    division: str | None = None
    season: int
    coach: str | None = None
    stadium: str | None = None
    offensive_context: dict[str, Any] = Field(default_factory=dict)
    defensive_context: dict[str, Any] = Field(default_factory=dict)


class GameRecord(BaseModel):
    game_id: str
    season: int
    week: int
    game_type: GameType
    date: date
    home_team_id: str
    away_team_id: str
    venue: str | None = None
    weather: dict[str, Any] = Field(default_factory=dict)
    final_score: dict[str, int] | None = None
    source: SourceMetadata


class WeeklyStatsRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_id: str
    game_id: str
    season: int
    week: int
    passing_yards: float = 0
    passing_touchdowns: int = 0
    interceptions_thrown: int = 0
    rushing_yards: float = 0
    rushing_touchdowns: int = 0
    receptions: int = 0
    receiving_yards: float = 0
    receiving_touchdowns: int = 0
    fantasy_points: float | None = None
    source_snapshot_id: str


class SeasonStatsRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    player_id: str
    season: int
    games: NonNegativeInt
    starts: NonNegativeInt = 0
    fantasy_points: float
    points_per_game: float | None = None
    weekly_median: float | None = None
    weekly_stddev: NonNegativeFloat | None = None


class ProjectionRecord(BaseModel):
    projection_id: str
    player_id: str
    season: int
    scope: Literal["season", "week"] = "season"
    week: int | None = None
    mean: float
    median: float
    lower_quantile: float
    upper_quantile: float
    games_played_mean: NonNegativeFloat | None = None
    model_version: str
    data_snapshot_id: str
    generated_at: datetime

    @field_validator("upper_quantile")
    @classmethod
    def upper_quantile_must_not_be_less_than_lower(
        cls, upper_quantile: float, info: Any
    ) -> float:
        lower_quantile = info.data.get("lower_quantile")
        if lower_quantile is not None and upper_quantile < lower_quantile:
            raise ValueError("upper_quantile must be greater than or equal to lower_quantile")
        return upper_quantile

    def model_post_init(self, __context: Any) -> None:
        if self.scope == "week" and self.week is None:
            raise ValueError("week is required for weekly projections")


class ADPRecord(BaseModel):
    adp_id: str
    player_id: str
    source: str
    format: str
    scoring: str
    date: date
    overall_adp: NonNegativeFloat
    position_adp: NonNegativeFloat | None = None
    rank: NonNegativeInt | None = None
    sample_size: NonNegativeInt | None = None
    snapshot_id: str


class InjuryRecord(BaseModel):
    injury_id: str
    player_id: str
    report_date: date
    body_part: str | None = None
    status: str
    practice_participation: str | None = None
    expected_return: date | None = None
    source: str
    source_timestamp: datetime
    confidence: float = Field(ge=0, le=1)


class DraftPickRecord(BaseModel):
    draft_id: str
    overall_pick: int
    round: int
    round_pick: int
    manager_id: str
    player_id: str
    timestamp: datetime | None = None
    source: str = "manual"
    manually_entered: bool = True
    corrected: bool = False
    prior_pick_reference: int | None = None


class RosterRecord(BaseModel):
    manager_id: str
    player_ids: list[str]
    starting_slots: dict[str, str | None] = Field(default_factory=dict)
    bench_slots: list[str] = Field(default_factory=list)
    ir_slots: list[str] = Field(default_factory=list)
    positional_counts: dict[str, int] = Field(default_factory=dict)
    vacancies: dict[str, int] = Field(default_factory=dict)
    strength_summary: dict[str, float] = Field(default_factory=dict)


class DraftStateRecord(BaseModel):
    draft_id: str
    current_pick: int
    current_round: int
    manager_on_clock: str
    completed_picks: list[DraftPickRecord]
    available_player_ids: list[str]
    rosters: dict[str, RosterRecord]
    user_future_picks: list[int]
    undo_stack: list[list[DraftPickRecord]] = Field(default_factory=list)
    redo_stack: list[list[DraftPickRecord]] = Field(default_factory=list)
    model_version: str | None = None
    data_snapshot_id: str
    simulation_seed: int | None = None
    updated_at: datetime


class RecommendationRecord(BaseModel):
    recommendation_id: str
    draft_state_id: str
    candidate_player_id: str
    rank: int
    expected_utility: float
    playoff_probability: float = Field(ge=0, le=1)
    championship_probability: float = Field(ge=0, le=1)
    next_pick_availability: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    explanation_components: list[str]
    model_version: str
    simulation_seed: int | None = None
    generated_at: datetime


class SimulationResultRecord(BaseModel):
    simulation_id: str
    draft_state_id: str
    candidate_player_id: str
    simulation_count: PositiveInt
    seed: int
    expected_roster_value: float
    playoff_probability: float = Field(ge=0, le=1)
    championship_probability: float = Field(ge=0, le=1)
    downside_metric: float
    runtime_seconds: NonNegativeFloat
    model_versions: dict[str, str]
    snapshot_id: str


class DataSnapshotRecord(BaseModel):
    snapshot_id: str
    dataset_name: str
    source: str
    retrieval_timestamp: datetime
    season: int
    checksum: str
    raw_path: str | None = None
    processed_path: str
    schema_version: str
    preprocessing_version: str
    license_notes: str
    source_url: str | None = None
    row_count: NonNegativeInt

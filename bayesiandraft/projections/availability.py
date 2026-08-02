from pydantic import BaseModel, Field

from bayesiandraft.domain import InjuryRecord
from bayesiandraft.projections.baseline import PlayerProjectionDistribution

INJURY_STATUS_AVAILABILITY: dict[str, float] = {
    "healthy": 1.0,
    "active": 1.0,
    "probable": 0.95,
    "questionable": 0.75,
    "doubtful": 0.35,
    "out": 0.0,
    "ir": 0.0,
    "pup": 0.2,
    "suspended": 0.0,
}


class GamesPlayedEstimate(BaseModel):
    player_id: str
    base_games_played: float
    availability_probability: float = Field(ge=0, le=1)
    adjusted_games_played: float
    adjusted_season_mean: float
    risk_label: str
    explanation: list[str]


def estimate_games_played(
    distribution: PlayerProjectionDistribution,
    injuries: list[InjuryRecord],
) -> GamesPlayedEstimate:
    player_injuries = [injury for injury in injuries if injury.player_id == distribution.player_id]
    availability = 1.0
    explanation = ["No active injury adjustment."]

    if player_injuries:
        latest = max(player_injuries, key=lambda injury: injury.source_timestamp)
        availability = _availability_for_status(latest.status) * latest.confidence
        explanation = [
            f"Latest injury status is {latest.status}.",
            f"Source confidence is {latest.confidence:.2f}.",
        ]

    adjusted_games = distribution.games_played_mean * availability
    adjusted_mean = distribution.season_mean * availability
    return GamesPlayedEstimate(
        player_id=distribution.player_id,
        base_games_played=round(distribution.games_played_mean, 4),
        availability_probability=round(availability, 4),
        adjusted_games_played=round(adjusted_games, 4),
        adjusted_season_mean=round(adjusted_mean, 4),
        risk_label=_risk_label(availability),
        explanation=explanation,
    )


def estimate_all_games_played(
    distributions: list[PlayerProjectionDistribution],
    injuries: list[InjuryRecord],
) -> list[GamesPlayedEstimate]:
    return [
        estimate_games_played(distribution, injuries)
        for distribution in distributions
    ]


def _availability_for_status(status: str) -> float:
    return INJURY_STATUS_AVAILABILITY.get(status.strip().lower(), 0.85)


def _risk_label(availability_probability: float) -> str:
    if availability_probability >= 0.9:
        return "low"
    if availability_probability >= 0.6:
        return "medium"
    return "high"

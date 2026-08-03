import math

from pydantic import BaseModel, Field


class BacktestObservation(BaseModel):
    observation_id: str
    predicted_rank: int
    actual_rank: int
    predicted_probability: float = Field(ge=0, le=1)
    outcome: bool


class BacktestSummary(BaseModel):
    observation_count: int
    mean_absolute_rank_error: float
    brier_score: float
    log_loss: float


def mean_absolute_rank_error(observations: list[BacktestObservation]) -> float:
    if not observations:
        return 0
    total_error = sum(
        abs(observation.predicted_rank - observation.actual_rank)
        for observation in observations
    )
    return round(total_error / len(observations), 4)


def brier_score(observations: list[BacktestObservation]) -> float:
    if not observations:
        return 0
    total_error = sum(
        (observation.predicted_probability - float(observation.outcome)) ** 2
        for observation in observations
    )
    return round(total_error / len(observations), 4)


def log_loss(observations: list[BacktestObservation]) -> float:
    if not observations:
        return 0
    epsilon = 1e-15
    total_loss = 0.0
    for observation in observations:
        probability = min(max(observation.predicted_probability, epsilon), 1 - epsilon)
        outcome = float(observation.outcome)
        total_loss += -(outcome * math.log(probability) + (1 - outcome) * math.log(1 - probability))
    return round(total_loss / len(observations), 4)


def summarize_backtest(observations: list[BacktestObservation]) -> BacktestSummary:
    return BacktestSummary(
        observation_count=len(observations),
        mean_absolute_rank_error=mean_absolute_rank_error(observations),
        brier_score=brier_score(observations),
        log_loss=log_loss(observations),
    )

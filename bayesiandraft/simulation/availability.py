import math
import random

from pydantic import BaseModel, Field

from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import RankingRow


class AvailabilityConfig(BaseModel):
    adp_stddev: float = 12.0
    roster_need_weight: float = 4.0
    position_run_weight: float = 2.5
    simulation_count: int = Field(default=500, ge=1)


class AvailabilityEstimate(BaseModel):
    player_id: str
    target_pick: int
    probability: float
    simulation_count: int
    seed: int


def estimate_availability(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    player_id: str,
    target_pick: int | None = None,
    seed: int = 1,
    config: AvailabilityConfig | None = None,
) -> AvailabilityEstimate:
    model_config = config or AvailabilityConfig()
    target = target_pick or _next_user_pick(draft_state)
    if target <= draft_state.current_overall_pick:
        return AvailabilityEstimate(
            player_id=player_id,
            target_pick=target,
            probability=0,
            simulation_count=model_config.simulation_count,
            seed=seed,
        )

    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    if player_id not in ranking_by_id:
        raise ValueError("unknown player_id")
    if player_id not in draft_state.available_player_ids:
        return AvailabilityEstimate(
            player_id=player_id,
            target_pick=target,
            probability=0,
            simulation_count=model_config.simulation_count,
            seed=seed,
        )

    rng = random.Random(seed)
    survived_count = 0
    available_ids = set(draft_state.available_player_ids)
    candidate_ids = [
        ranking.player_id for ranking in rankings if ranking.player_id in available_ids
    ]
    recent_positions = _recent_positions(draft_state, ranking_by_id)

    for _ in range(model_config.simulation_count):
        simulated_available = set(candidate_ids)
        for overall_pick in range(draft_state.current_overall_pick, target):
            if player_id not in simulated_available:
                break
            selected = _sample_pick(
                simulated_available,
                rankings=ranking_by_id,
                overall_pick=overall_pick,
                recent_positions=recent_positions,
                rng=rng,
                config=model_config,
            )
            simulated_available.remove(selected)
        if player_id in simulated_available:
            survived_count += 1

    return AvailabilityEstimate(
        player_id=player_id,
        target_pick=target,
        probability=round(survived_count / model_config.simulation_count, 4),
        simulation_count=model_config.simulation_count,
        seed=seed,
    )


def estimate_all_availability(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    seed: int = 1,
    config: AvailabilityConfig | None = None,
) -> list[AvailabilityEstimate]:
    return [
        estimate_availability(
            draft_state,
            rankings,
            player_id=ranking.player_id,
            seed=seed + index,
            config=config,
        )
        for index, ranking in enumerate(rankings)
        if ranking.player_id in draft_state.available_player_ids
    ]


def _sample_pick(
    available_ids: set[str],
    *,
    rankings: dict[str, RankingRow],
    overall_pick: int,
    recent_positions: list[str],
    rng: random.Random,
    config: AvailabilityConfig,
) -> str:
    weights = []
    ids = list(available_ids)
    for player_id in ids:
        ranking = rankings[player_id]
        adp = ranking.adp or ranking.overall_rank
        adp_pressure = math.exp(-((adp - overall_pick) ** 2) / (2 * config.adp_stddev**2))
        rank_pressure = 1 / max(ranking.overall_rank, 1)
        run_bonus = config.position_run_weight if ranking.position.value in recent_positions else 0
        need_bonus = (
            config.roster_need_weight if ranking.position.value in {"RB", "WR", "TE"} else 0
        )
        weights.append(max(adp_pressure + rank_pressure + run_bonus + need_bonus, 0.001))
    return rng.choices(ids, weights=weights, k=1)[0]


def _next_user_pick(draft_state: DraftState) -> int:
    if not draft_state.user_future_picks:
        return draft_state.current_overall_pick
    return draft_state.user_future_picks[0].overall_pick


def _recent_positions(
    draft_state: DraftState,
    rankings: dict[str, RankingRow],
    *,
    window: int = 4,
) -> list[str]:
    positions = []
    for pick in draft_state.completed_picks[-window:]:
        ranking = rankings.get(pick.player_id)
        if ranking is not None:
            positions.append(ranking.position.value)
    return positions

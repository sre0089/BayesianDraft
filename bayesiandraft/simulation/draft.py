import math
import random
from collections import Counter

from pydantic import BaseModel, Field, PositiveInt

from bayesiandraft.draft import DraftPick, DraftState
from bayesiandraft.rankings import RankingRow


class DraftSimulationConfig(BaseModel):
    simulation_count: PositiveInt = 100
    seed: int = 1
    adp_stddev: float = 14.0
    roster_need_weight: float = 4.0
    candidate_limit: PositiveInt = 250


class SimulatedDraft(BaseModel):
    seed: int
    completed_picks: list[DraftPick]
    remaining_player_ids: list[str]
    stopped_reason: str


class CandidateRolloutResult(BaseModel):
    candidate_player_id: str
    simulation_count: int
    seed: int
    average_projected_points: float
    average_vorp: float
    average_roster_size: float
    roster_position_counts: dict[str, float] = Field(default_factory=dict)


def simulate_remaining_draft(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    seed: int = 1,
    config: DraftSimulationConfig | None = None,
) -> SimulatedDraft:
    simulation_config = config or DraftSimulationConfig(seed=seed)
    rng = random.Random(seed)
    ranking_by_id = _ranking_by_id(rankings, draft_state)
    state = draft_state

    while not state.is_complete:
        available_ids = [
            ranking.player_id
            for ranking in rankings[: simulation_config.candidate_limit]
            if ranking.player_id in state.available_player_ids
        ]
        if not available_ids:
            return _simulated_draft(state, seed=seed, stopped_reason="no_ranked_players_available")

        selected = _sample_player(
            available_ids,
            state=state,
            rankings=ranking_by_id,
            rng=rng,
            config=simulation_config,
        )
        state = state.record_pick(selected)

    return _simulated_draft(state, seed=seed, stopped_reason="draft_complete")


def simulate_candidate_rollout(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    candidate_player_id: str,
    config: DraftSimulationConfig | None = None,
) -> CandidateRolloutResult:
    simulation_config = config or DraftSimulationConfig()
    if candidate_player_id not in draft_state.available_player_ids:
        raise ValueError("candidate_player_id must be available")
    if draft_state.manager_on_clock != draft_state.league_config.league.user_manager_id:
        raise ValueError("candidate rollouts require the user manager to be on clock")

    ranking_by_id = _ranking_by_id(rankings, draft_state)
    if candidate_player_id not in ranking_by_id:
        raise ValueError("candidate_player_id must exist in rankings")

    user_manager_id = draft_state.league_config.league.user_manager_id
    projected_points: list[float] = []
    vorp_values: list[float] = []
    roster_sizes: list[int] = []
    position_totals: Counter[str] = Counter()

    for offset in range(simulation_config.simulation_count):
        seed = simulation_config.seed + offset
        candidate_state = draft_state.record_pick(candidate_player_id)
        simulated = simulate_remaining_draft(
            candidate_state,
            rankings,
            seed=seed,
            config=simulation_config,
        )
        roster = _roster_for_completed_picks(
            simulated.completed_picks,
            user_manager_id=user_manager_id,
        )
        roster_rows = [
            ranking_by_id[player_id]
            for player_id in roster
            if player_id in ranking_by_id
        ]
        projected_points.append(sum(row.projected_points for row in roster_rows))
        vorp_values.append(sum(row.vorp for row in roster_rows))
        roster_sizes.append(len(roster_rows))
        position_totals.update(row.position.value for row in roster_rows)

    return CandidateRolloutResult(
        candidate_player_id=candidate_player_id,
        simulation_count=simulation_config.simulation_count,
        seed=simulation_config.seed,
        average_projected_points=round(_mean(projected_points), 4),
        average_vorp=round(_mean(vorp_values), 4),
        average_roster_size=round(_mean(roster_sizes), 4),
        roster_position_counts={
            position: round(count / simulation_config.simulation_count, 4)
            for position, count in sorted(position_totals.items())
        },
    )


def _sample_player(
    available_ids: list[str],
    *,
    state: DraftState,
    rankings: dict[str, RankingRow],
    rng: random.Random,
    config: DraftSimulationConfig,
) -> str:
    overall_pick = state.current_overall_pick
    manager_id = state.manager_on_clock
    weights = []
    for player_id in available_ids:
        ranking = rankings[player_id]
        adp = ranking.adp or ranking.overall_rank
        adp_pressure = math.exp(-((adp - overall_pick) ** 2) / (2 * config.adp_stddev**2))
        rank_pressure = 1 / max(ranking.overall_rank, 1)
        value_pressure = max(ranking.vorp, 0) / 100
        need_bonus = _manager_need_bonus(state, manager_id, ranking, config)
        weights.append(max(adp_pressure + rank_pressure + value_pressure + need_bonus, 0.001))
    return rng.choices(available_ids, weights=weights, k=1)[0]


def _manager_need_bonus(
    state: DraftState,
    manager_id: str | None,
    ranking: RankingRow,
    config: DraftSimulationConfig,
) -> float:
    if manager_id is None:
        return 0

    roster = state.rosters.get(manager_id)
    current_count = 0 if roster is None else roster.positional_counts.get(ranking.position.value, 0)
    starter_target = state.league_config.roster.starting_slots.get(ranking.position.value, 0)
    if current_count < starter_target:
        return config.roster_need_weight
    return 0


def _ranking_by_id(
    rankings: list[RankingRow],
    draft_state: DraftState,
) -> dict[str, RankingRow]:
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    missing_rankings = set(draft_state.available_player_ids) - set(ranking_by_id)
    if missing_rankings:
        raise ValueError("all available players must exist in rankings")
    return ranking_by_id


def _simulated_draft(state: DraftState, *, seed: int, stopped_reason: str) -> SimulatedDraft:
    return SimulatedDraft(
        seed=seed,
        completed_picks=state.completed_picks,
        remaining_player_ids=state.available_player_ids,
        stopped_reason=stopped_reason,
    )


def _roster_for_completed_picks(
    completed_picks: list[DraftPick],
    *,
    user_manager_id: str,
) -> list[str]:
    return [
        pick.player_id
        for pick in completed_picks
        if pick.manager_id == user_manager_id
    ]


def _mean(values: list[float] | list[int]) -> float:
    if not values:
        return 0
    return sum(values) / len(values)

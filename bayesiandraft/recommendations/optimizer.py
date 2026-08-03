from pydantic import BaseModel, Field, PositiveInt

from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import RankingRow
from bayesiandraft.simulation import DraftSimulationConfig, simulate_candidate_rollout


class CandidateOptimizerConfig(BaseModel):
    limit: PositiveInt = 4
    candidate_pool_size: PositiveInt = 8
    simulation_count: PositiveInt = 25
    seed: int = 1


class OptimizedCandidate(BaseModel):
    player_id: str
    rank: int
    optimizer_score: float
    average_projected_points: float
    average_vorp: float
    average_roster_size: float
    roster_position_counts: dict[str, float] = Field(default_factory=dict)
    explanation: list[str]


class CandidateOptimizationResult(BaseModel):
    primary: OptimizedCandidate
    alternatives: list[OptimizedCandidate]
    simulation_count: int
    seed: int


def optimize_candidates(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    config: CandidateOptimizerConfig | None = None,
) -> CandidateOptimizationResult:
    optimizer_config = config or CandidateOptimizerConfig()
    if draft_state.manager_on_clock != draft_state.league_config.league.user_manager_id:
        raise ValueError("candidate optimization requires the user manager to be on clock")

    available_ids = set(draft_state.available_player_ids)
    candidate_rankings = [
        ranking
        for ranking in rankings
        if ranking.player_id in available_ids
    ][: optimizer_config.candidate_pool_size]
    if not candidate_rankings:
        raise ValueError("no available players to optimize")

    optimized = [
        _optimize_candidate(
            draft_state,
            rankings,
            candidate_ranking=ranking,
            seed=optimizer_config.seed + index,
            simulation_count=optimizer_config.simulation_count,
        )
        for index, ranking in enumerate(candidate_rankings)
    ]
    optimized.sort(key=lambda candidate: (-candidate.optimizer_score, candidate.rank))

    return CandidateOptimizationResult(
        primary=optimized[0],
        alternatives=optimized[1 : optimizer_config.limit],
        simulation_count=optimizer_config.simulation_count,
        seed=optimizer_config.seed,
    )


def _optimize_candidate(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    candidate_ranking: RankingRow,
    seed: int,
    simulation_count: int,
) -> OptimizedCandidate:
    rollout = simulate_candidate_rollout(
        draft_state,
        rankings,
        candidate_player_id=candidate_ranking.player_id,
        config=DraftSimulationConfig(simulation_count=simulation_count, seed=seed),
    )
    optimizer_score = (
        rollout.average_vorp
        + candidate_ranking.vorp * 0.25
        + max(candidate_ranking.adp_delta or 0, 0) * 0.2
    )

    return OptimizedCandidate(
        player_id=candidate_ranking.player_id,
        rank=candidate_ranking.overall_rank,
        optimizer_score=round(optimizer_score, 4),
        average_projected_points=rollout.average_projected_points,
        average_vorp=rollout.average_vorp,
        average_roster_size=rollout.average_roster_size,
        roster_position_counts=rollout.roster_position_counts,
        explanation=_explain_candidate(candidate_ranking, rollout.average_vorp),
    )


def _explain_candidate(ranking: RankingRow, average_vorp: float) -> list[str]:
    explanation = [
        f"Rollout roster averages {average_vorp:.1f} VORP.",
        (
            f"Candidate ranks {ranking.overall_rank} overall and "
            f"{ranking.position_rank} at {ranking.position}."
        ),
    ]
    if ranking.adp_delta is not None and ranking.adp_delta > 0:
        explanation.append(f"Market is {ranking.adp_delta:.1f} picks later than model rank.")
    if ranking.tier == 1:
        explanation.append("Candidate is still in the top positional tier.")
    return explanation

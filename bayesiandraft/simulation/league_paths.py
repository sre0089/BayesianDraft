from collections import defaultdict
from collections.abc import Callable
from statistics import median, pstdev

from pydantic import BaseModel, Field, PositiveInt

from bayesiandraft.draft import DraftPick, DraftState
from bayesiandraft.rankings import RankingRow
from bayesiandraft.simulation.draft import DraftSimulationConfig, simulate_remaining_draft


class LeaguePathSimulationConfig(BaseModel):
    simulation_count: PositiveInt = 100
    seed: int = 1
    draft_config: DraftSimulationConfig = Field(default_factory=DraftSimulationConfig)


class ManagerPathSummary(BaseModel):
    manager_id: str
    average_projected_points: float
    average_vorp: float
    median_vorp: float
    best_vorp: float
    worst_vorp: float
    vorp_volatility: float
    average_finish: float
    top_three_rate: float
    first_place_rate: float


class UserRiskSummary(BaseModel):
    best_case_vorp: float
    median_vorp: float
    worst_case_vorp: float
    vorp_volatility: float
    average_finish: float
    top_three_rate: float
    first_place_rate: float


class LeaguePathAnalysisResult(BaseModel):
    simulation_count: int
    seed: int
    manager_results: list[ManagerPathSummary]
    user_risk: UserRiskSummary
    stopped_reasons: dict[str, int] = Field(default_factory=dict)


class LeaguePathProgress(BaseModel):
    completed_paths: int
    total_paths: int
    seed: int
    stopped_reason: str
    current_leader_id: str
    current_leader_vorp: float


LeaguePathProgressCallback = Callable[[LeaguePathProgress], None]


def analyze_league_paths(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    config: LeaguePathSimulationConfig | None = None,
    progress_callback: LeaguePathProgressCallback | None = None,
) -> LeaguePathAnalysisResult:
    analysis_config = config or LeaguePathSimulationConfig()
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    manager_ids = [manager.id for manager in draft_state.league_config.draft_order]
    projected_points_by_manager: dict[str, list[float]] = defaultdict(list)
    vorp_by_manager: dict[str, list[float]] = defaultdict(list)
    finish_by_manager: dict[str, list[int]] = defaultdict(list)
    stopped_reasons: dict[str, int] = defaultdict(int)

    for offset in range(analysis_config.simulation_count):
        seed = analysis_config.seed + offset
        simulated = simulate_remaining_draft(
            draft_state,
            rankings,
            seed=seed,
            config=analysis_config.draft_config.model_copy(update={"seed": seed}),
        )
        stopped_reasons[simulated.stopped_reason] += 1
        path_scores = _score_path(
            simulated.completed_picks,
            manager_ids=manager_ids,
            ranking_by_id=ranking_by_id,
        )
        finishes = _finish_ranks(path_scores)
        if progress_callback is not None:
            leader_id = min(finishes, key=lambda manager_id: finishes[manager_id])
            progress_callback(
                LeaguePathProgress(
                    completed_paths=offset + 1,
                    total_paths=analysis_config.simulation_count,
                    seed=seed,
                    stopped_reason=simulated.stopped_reason,
                    current_leader_id=leader_id,
                    current_leader_vorp=round(path_scores[leader_id].vorp, 4),
                )
            )
        for manager_id in manager_ids:
            score = path_scores[manager_id]
            projected_points_by_manager[manager_id].append(score.projected_points)
            vorp_by_manager[manager_id].append(score.vorp)
            finish_by_manager[manager_id].append(finishes[manager_id])

    manager_results = [
        _manager_summary(
            manager_id,
            projected_points_by_manager[manager_id],
            vorp_by_manager[manager_id],
            finish_by_manager[manager_id],
        )
        for manager_id in manager_ids
    ]
    manager_results.sort(key=lambda summary: (summary.average_finish, -summary.average_vorp))
    user_manager_id = draft_state.league_config.league.user_manager_id

    return LeaguePathAnalysisResult(
        simulation_count=analysis_config.simulation_count,
        seed=analysis_config.seed,
        manager_results=manager_results,
        user_risk=_user_risk_summary(
            vorp_by_manager[user_manager_id],
            finish_by_manager[user_manager_id],
        ),
        stopped_reasons=dict(sorted(stopped_reasons.items())),
    )


class _PathScore(BaseModel):
    projected_points: float = 0
    vorp: float = 0


def _score_path(
    completed_picks: list[DraftPick],
    *,
    manager_ids: list[str],
    ranking_by_id: dict[str, RankingRow],
) -> dict[str, _PathScore]:
    scores = {manager_id: _PathScore() for manager_id in manager_ids}
    for pick in completed_picks:
        ranking = ranking_by_id.get(pick.player_id)
        if ranking is None:
            continue
        score = scores[pick.manager_id]
        score.projected_points += ranking.projected_points
        score.vorp += ranking.vorp
    return scores


def _finish_ranks(path_scores: dict[str, _PathScore]) -> dict[str, int]:
    ordered = sorted(
        path_scores.items(),
        key=lambda item: (-item[1].vorp, -item[1].projected_points, item[0]),
    )
    return {manager_id: index for index, (manager_id, _score) in enumerate(ordered, start=1)}


def _manager_summary(
    manager_id: str,
    projected_points: list[float],
    vorp: list[float],
    finishes: list[int],
) -> ManagerPathSummary:
    return ManagerPathSummary(
        manager_id=manager_id,
        average_projected_points=round(_mean(projected_points), 4),
        average_vorp=round(_mean(vorp), 4),
        median_vorp=round(median(vorp), 4) if vorp else 0,
        best_vorp=round(max(vorp), 4) if vorp else 0,
        worst_vorp=round(min(vorp), 4) if vorp else 0,
        vorp_volatility=round(pstdev(vorp), 4) if len(vorp) > 1 else 0,
        average_finish=round(_mean(finishes), 4),
        top_three_rate=round(_rate(finishes, threshold=3), 4),
        first_place_rate=round(_rate(finishes, threshold=1), 4),
    )


def _user_risk_summary(vorp: list[float], finishes: list[int]) -> UserRiskSummary:
    return UserRiskSummary(
        best_case_vorp=round(max(vorp), 4) if vorp else 0,
        median_vorp=round(median(vorp), 4) if vorp else 0,
        worst_case_vorp=round(min(vorp), 4) if vorp else 0,
        vorp_volatility=round(pstdev(vorp), 4) if len(vorp) > 1 else 0,
        average_finish=round(_mean(finishes), 4),
        top_three_rate=round(_rate(finishes, threshold=3), 4),
        first_place_rate=round(_rate(finishes, threshold=1), 4),
    )


def _mean(values: list[float] | list[int]) -> float:
    if not values:
        return 0
    return sum(values) / len(values)


def _rate(finishes: list[int], *, threshold: int) -> float:
    if not finishes:
        return 0
    return sum(1 for finish in finishes if finish <= threshold) / len(finishes)

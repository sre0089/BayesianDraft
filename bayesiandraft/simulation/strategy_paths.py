from pydantic import BaseModel, Field, PositiveInt

from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import RankingRow
from bayesiandraft.simulation.draft import DraftSimulationConfig
from bayesiandraft.simulation.league_paths import (
    LeaguePathSimulationConfig,
    ManagerPathSummary,
    UserRiskSummary,
    analyze_league_paths,
)


class StrategyPathSimulationConfig(BaseModel):
    simulation_count: PositiveInt = 50
    seed: int = 1
    positions: tuple[str, ...] = ("RB", "WR", "QB", "TE")
    draft_config: DraftSimulationConfig = Field(default_factory=DraftSimulationConfig)


class StrategyPathSummary(BaseModel):
    label: str
    position: str
    forced_player_id: str
    forced_player_name: str
    average_projected_points: float
    average_vorp: float
    median_vorp: float
    downside_vorp: float
    top_three_rate: float
    first_place_rate: float
    average_finish: float


class StrategyPathAnalysisResult(BaseModel):
    simulation_count: int
    seed: int
    paths: list[StrategyPathSummary]


def analyze_user_strategy_paths(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    config: StrategyPathSimulationConfig | None = None,
) -> StrategyPathAnalysisResult:
    strategy_config = config or StrategyPathSimulationConfig()
    user_manager_id = draft_state.league_config.league.user_manager_id
    if draft_state.manager_on_clock != user_manager_id:
        return StrategyPathAnalysisResult(
            simulation_count=strategy_config.simulation_count,
            seed=strategy_config.seed,
            paths=[],
        )

    available_ids = set(draft_state.available_player_ids)
    paths: list[StrategyPathSummary] = []
    for index, position in enumerate(strategy_config.positions):
        candidate = _best_available_at_position(rankings, available_ids, position)
        if candidate is None:
            continue
        candidate_state = draft_state.record_pick(candidate.player_id)
        league_result = analyze_league_paths(
            candidate_state,
            rankings,
            config=LeaguePathSimulationConfig(
                simulation_count=strategy_config.simulation_count,
                seed=strategy_config.seed + index * strategy_config.simulation_count,
                draft_config=strategy_config.draft_config.model_copy(
                    update={
                        "simulation_count": strategy_config.simulation_count,
                        "seed": strategy_config.seed + index * strategy_config.simulation_count,
                    }
                ),
            ),
        )
        user_result = next(
            result
            for result in league_result.manager_results
            if result.manager_id == user_manager_id
        )
        paths.append(_strategy_summary(candidate, user_result, league_result.user_risk))

    paths.sort(key=lambda path: (-path.average_vorp, path.average_finish, path.position))
    return StrategyPathAnalysisResult(
        simulation_count=strategy_config.simulation_count,
        seed=strategy_config.seed,
        paths=paths,
    )


def _best_available_at_position(
    rankings: list[RankingRow],
    available_ids: set[str],
    position: str,
) -> RankingRow | None:
    for ranking in rankings:
        if ranking.player_id in available_ids and ranking.position.value == position:
            return ranking
    return None


def _strategy_summary(
    candidate: RankingRow,
    user_result: ManagerPathSummary,
    user_risk: UserRiskSummary,
) -> StrategyPathSummary:
    return StrategyPathSummary(
        label=f"{candidate.position.value} early path",
        position=candidate.position.value,
        forced_player_id=candidate.player_id,
        forced_player_name=candidate.full_name,
        average_projected_points=user_result.average_projected_points,
        average_vorp=user_result.average_vorp,
        median_vorp=user_risk.median_vorp,
        downside_vorp=user_risk.worst_case_vorp,
        top_three_rate=user_result.top_three_rate,
        first_place_rate=user_result.first_place_rate,
        average_finish=user_result.average_finish,
    )

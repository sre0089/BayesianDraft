from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from statistics import median

from pydantic import BaseModel, Field, PositiveInt

from bayesiandraft.draft import DraftPick, DraftState, Player
from bayesiandraft.rankings import RankingRow
from bayesiandraft.simulation.draft import DraftSimulationConfig, simulate_remaining_draft
from bayesiandraft.simulation.roster_strength import score_roster_strength


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


class StrategyPathProgress(BaseModel):
    completed_paths: int
    total_paths: int
    board_sample: int
    position: str
    forced_player_name: str | None


StrategyPathProgressCallback = Callable[[StrategyPathProgress], None]


class _StrategyOutcome(BaseModel):
    forced_player_id: str
    forced_player_name: str
    projected_points: float
    vorp: float
    finish: int


class _RosterScore(BaseModel):
    projected_points: float = 0
    vorp: float = 0


def analyze_user_strategy_paths(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    config: StrategyPathSimulationConfig | None = None,
    progress_callback: StrategyPathProgressCallback | None = None,
) -> StrategyPathAnalysisResult:
    strategy_config = config or StrategyPathSimulationConfig()
    user_manager_id = draft_state.league_config.league.user_manager_id
    if not draft_state.user_future_picks:
        return StrategyPathAnalysisResult(
            simulation_count=strategy_config.simulation_count,
            seed=strategy_config.seed,
            paths=[],
        )

    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    outcomes_by_position: dict[str, list[_StrategyOutcome]] = defaultdict(list)
    positions = tuple(dict.fromkeys(strategy_config.positions))
    total_paths = strategy_config.simulation_count * max(len(positions), 1)
    completed_paths = 0

    for sample_index in range(strategy_config.simulation_count):
        arrival_state = _state_at_next_user_pick(
            draft_state,
            rankings,
            seed=strategy_config.seed + sample_index,
            config=strategy_config.draft_config,
        )
        available_ids = set(arrival_state.available_player_ids)
        for position_index, position in enumerate(positions):
            candidate = _best_available_at_position(rankings, available_ids, position)
            if candidate is None:
                completed_paths += 1
                if progress_callback is not None:
                    progress_callback(
                        StrategyPathProgress(
                            completed_paths=completed_paths,
                            total_paths=total_paths,
                            board_sample=sample_index + 1,
                            position=position,
                            forced_player_name=None,
                        )
                    )
                continue
            forced_state = arrival_state.record_pick(candidate.player_id)
            simulated = simulate_remaining_draft(
                forced_state,
                rankings,
                seed=strategy_config.seed
                + strategy_config.simulation_count
                + sample_index * max(len(positions), 1)
                + position_index,
                config=strategy_config.draft_config,
            )
            roster_scores = _score_managers(
                simulated.completed_picks,
                manager_ids=[manager.id for manager in draft_state.league_config.draft_order],
                ranking_by_id=ranking_by_id,
                draft_state=draft_state,
            )
            finishes = _finish_ranks(roster_scores)
            user_score = roster_scores[user_manager_id]
            outcomes_by_position[position].append(
                _StrategyOutcome(
                    forced_player_id=candidate.player_id,
                    forced_player_name=candidate.full_name,
                    projected_points=user_score.projected_points,
                    vorp=user_score.vorp,
                    finish=finishes[user_manager_id],
                )
            )
            completed_paths += 1
            if progress_callback is not None:
                progress_callback(
                    StrategyPathProgress(
                        completed_paths=completed_paths,
                        total_paths=total_paths,
                        board_sample=sample_index + 1,
                        position=position,
                        forced_player_name=candidate.full_name,
                    )
                )

    paths = [
        _strategy_summary(position, outcomes)
        for position, outcomes in outcomes_by_position.items()
        if outcomes
    ]
    paths.sort(key=lambda path: (-path.average_vorp, path.average_finish, path.position))
    return StrategyPathAnalysisResult(
        simulation_count=strategy_config.simulation_count,
        seed=strategy_config.seed,
        paths=paths,
    )


def _state_at_next_user_pick(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    seed: int,
    config: DraftSimulationConfig,
) -> DraftState:
    if draft_state.manager_on_clock == draft_state.league_config.league.user_manager_id:
        return draft_state

    next_user_pick = draft_state.user_future_picks[0].overall_pick
    simulated = simulate_remaining_draft(
        draft_state,
        rankings,
        seed=seed,
        config=config,
    )
    picks_before_user = [
        pick for pick in simulated.completed_picks if pick.overall_pick < next_user_pick
    ]
    return _replay_state(draft_state, picks_before_user)


def _replay_state(template_state: DraftState, picks: list[DraftPick]) -> DraftState:
    state = DraftState.create(
        template_state.league_config,
        [
            Player(
                player_id=player.player_id,
                full_name=player.full_name,
                position=player.position,
                nfl_team_id=player.nfl_team_id,
            )
            for player in template_state.players.values()
        ],
        draft_id=f"{template_state.draft_id}-strategy-arrival",
        total_rounds=template_state.total_rounds,
    )
    for pick in sorted(picks, key=lambda item: item.overall_pick):
        state = state.record_pick(pick.player_id)
    return state


def _best_available_at_position(
    rankings: list[RankingRow],
    available_ids: set[str],
    position: str,
) -> RankingRow | None:
    for ranking in rankings:
        if ranking.player_id in available_ids and ranking.position.value == position:
            return ranking
    return None


def _score_managers(
    completed_picks: list[DraftPick],
    *,
    manager_ids: list[str],
    ranking_by_id: dict[str, RankingRow],
    draft_state: DraftState,
) -> dict[str, _RosterScore]:
    player_ids_by_manager: dict[str, list[str]] = {
        manager_id: [] for manager_id in manager_ids
    }
    for pick in completed_picks:
        if pick.manager_id in player_ids_by_manager:
            player_ids_by_manager[pick.manager_id].append(pick.player_id)
    scores = {}
    for manager_id, player_ids in player_ids_by_manager.items():
        strength = score_roster_strength(
            player_ids,
            rankings=ranking_by_id,
            league_config=draft_state.league_config,
        )
        scores[manager_id] = _RosterScore(
            projected_points=strength.projected_points,
            vorp=strength.vorp,
        )
    return scores


def _finish_ranks(roster_scores: dict[str, _RosterScore]) -> dict[str, int]:
    ordered = sorted(
        roster_scores.items(),
        key=lambda item: (-item[1].vorp, -item[1].projected_points, item[0]),
    )
    return {manager_id: index for index, (manager_id, _score) in enumerate(ordered, start=1)}


def _strategy_summary(
    position: str,
    outcomes: list[_StrategyOutcome],
) -> StrategyPathSummary:
    vorp_values = [outcome.vorp for outcome in outcomes]
    projected_points = [outcome.projected_points for outcome in outcomes]
    finishes = [outcome.finish for outcome in outcomes]
    forced_player_id = _most_common(outcome.forced_player_id for outcome in outcomes)
    forced_player_name = _most_common(outcome.forced_player_name for outcome in outcomes)
    return StrategyPathSummary(
        label=f"Next pick {position}",
        position=position,
        forced_player_id=forced_player_id,
        forced_player_name=forced_player_name,
        average_projected_points=round(_mean(projected_points), 4),
        average_vorp=round(_mean(vorp_values), 4),
        median_vorp=round(median(vorp_values), 4) if vorp_values else 0,
        downside_vorp=round(min(vorp_values), 4) if vorp_values else 0,
        top_three_rate=round(_rate(finishes, threshold=3), 4),
        first_place_rate=round(_rate(finishes, threshold=1), 4),
        average_finish=round(_mean(finishes), 4),
    )


def _most_common(values: Iterable[str]) -> str:
    return Counter(values).most_common(1)[0][0]


def _mean(values: list[float] | list[int]) -> float:
    if not values:
        return 0
    return sum(values) / len(values)


def _rate(finishes: list[int], *, threshold: int) -> float:
    if not finishes:
        return 0
    return sum(1 for finish in finishes if finish <= threshold) / len(finishes)

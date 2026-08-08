from pydantic import BaseModel, Field

from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import RankingRow
from bayesiandraft.recommendations import recommend_players


class DraftStrategyPickResult(BaseModel):
    overall_pick: int
    selected_player_id: str
    recommended_player_id: str
    accepted_primary: bool
    selected_vorp: float
    recommended_vorp: float


class DraftStrategyBacktestResult(BaseModel):
    pick_count: int
    user_pick_count: int
    accepted_primary_count: int
    accepted_primary_rate: float
    final_roster_vorp: float
    picks: list[DraftStrategyPickResult] = Field(default_factory=list)


def evaluate_recorded_draft_recommendations(
    completed_state: DraftState,
    rankings: list[RankingRow],
) -> DraftStrategyBacktestResult:
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    replay_state = DraftState.create(
        completed_state.league_config,
        list(completed_state.players.values()),
        draft_id=f"{completed_state.draft_id}-strategy-backtest",
        total_rounds=completed_state.total_rounds,
    )
    user_manager_id = completed_state.league_config.league.user_manager_id
    pick_results: list[DraftStrategyPickResult] = []

    for recorded_pick in completed_state.completed_picks:
        if replay_state.manager_on_clock == user_manager_id:
            recommendation = recommend_players(replay_state, rankings)
            selected_ranking = ranking_by_id.get(recorded_pick.player_id)
            recommended_ranking = ranking_by_id.get(recommendation.primary.player_id)
            pick_results.append(
                DraftStrategyPickResult(
                    overall_pick=recorded_pick.overall_pick,
                    selected_player_id=recorded_pick.player_id,
                    recommended_player_id=recommendation.primary.player_id,
                    accepted_primary=recorded_pick.player_id == recommendation.primary.player_id,
                    selected_vorp=0 if selected_ranking is None else selected_ranking.vorp,
                    recommended_vorp=0 if recommended_ranking is None else recommended_ranking.vorp,
                )
            )
        replay_state = replay_state.record_pick(recorded_pick.player_id)

    final_roster_vorp = sum(
        ranking_by_id[player_id].vorp
        for player_id in replay_state.rosters[user_manager_id].player_ids
        if player_id in ranking_by_id
    )
    accepted_primary_count = sum(1 for pick in pick_results if pick.accepted_primary)
    accepted_primary_rate = (
        0 if not pick_results else accepted_primary_count / len(pick_results)
    )

    return DraftStrategyBacktestResult(
        pick_count=len(completed_state.completed_picks),
        user_pick_count=len(pick_results),
        accepted_primary_count=accepted_primary_count,
        accepted_primary_rate=round(accepted_primary_rate, 4),
        final_roster_vorp=round(final_roster_vorp, 4),
        picks=pick_results,
    )

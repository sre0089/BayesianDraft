from pydantic import BaseModel

from bayesiandraft.draft.state import DraftState


class DraftStateSummary(BaseModel):
    draft_id: str
    current_overall_pick: int
    manager_on_clock: str | None
    completed_pick_count: int
    available_player_count: int
    user_roster_size: int
    next_user_pick: int | None


def summarize_draft_state(state: DraftState) -> DraftStateSummary:
    user_manager_id = state.league_config.league.user_manager_id
    next_user_pick = state.user_future_picks[0].overall_pick if state.user_future_picks else None
    return DraftStateSummary(
        draft_id=state.draft_id,
        current_overall_pick=state.current_overall_pick,
        manager_on_clock=state.manager_on_clock,
        completed_pick_count=len(state.completed_picks),
        available_player_count=len(state.available_player_ids),
        user_roster_size=len(state.rosters[user_manager_id].player_ids),
        next_user_pick=next_user_pick,
    )

from pydantic import BaseModel, Field

from bayesiandraft.draft import DraftPick, DraftState
from bayesiandraft.rankings import RankingRow


class OpponentModelConfig(BaseModel):
    smoothing: float = 1.0
    preference_weight: float = 3.0


class OpponentDraftProfile(BaseModel):
    manager_id: str
    picks_observed: int
    position_counts: dict[str, int] = Field(default_factory=dict)
    position_preferences: dict[str, float] = Field(default_factory=dict)
    risk_tolerance: float
    market_timing: float


def build_opponent_profiles(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    config: OpponentModelConfig | None = None,
) -> dict[str, OpponentDraftProfile]:
    model_config = config or OpponentModelConfig()
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    user_manager_id = draft_state.league_config.league.user_manager_id
    profiles = {}

    for manager in draft_state.league_config.draft_order:
        if manager.id == user_manager_id:
            continue
        manager_picks = [
            pick
            for pick in draft_state.completed_picks
            if pick.manager_id == manager.id and pick.player_id in ranking_by_id
        ]
        profiles[manager.id] = _profile_from_picks(
            manager.id,
            manager_picks=manager_picks,
            ranking_by_id=ranking_by_id,
            smoothing=model_config.smoothing,
        )

    return profiles


def opponent_pick_weight(
    manager_id: str | None,
    ranking: RankingRow,
    profiles: dict[str, OpponentDraftProfile],
    *,
    config: OpponentModelConfig | None = None,
) -> float:
    if manager_id is None:
        return 0

    profile = profiles.get(manager_id)
    if profile is None:
        return 0

    model_config = config or OpponentModelConfig()
    position_preference = profile.position_preferences.get(ranking.position.value, 0)
    market_fit = profile.market_timing * max(-(ranking.adp_delta or 0), 0) / 20
    return model_config.preference_weight * position_preference + market_fit


def _profile_from_picks(
    manager_id: str,
    *,
    manager_picks: list[DraftPick],
    ranking_by_id: dict[str, RankingRow],
    smoothing: float,
) -> OpponentDraftProfile:
    position_counts: dict[str, int] = {}
    adp_deltas = []
    for pick in manager_picks:
        ranking = ranking_by_id[pick.player_id]
        position = ranking.position.value
        position_counts[position] = position_counts.get(position, 0) + 1
        if ranking.adp_delta is not None:
            adp_deltas.append(ranking.adp_delta)

    positions = {ranking.position.value for ranking in ranking_by_id.values()}
    denominator = len(manager_picks) + smoothing * len(positions)
    position_preferences = {
        position: round((position_counts.get(position, 0) + smoothing) / denominator, 4)
        for position in sorted(positions)
    }
    average_adp_delta = sum(adp_deltas) / len(adp_deltas) if adp_deltas else 0
    market_timing = max(min(-average_adp_delta / 25, 1), -1)
    risk_tolerance = max(min(0.5 + len(manager_picks) / 20, 1), 0)

    return OpponentDraftProfile(
        manager_id=manager_id,
        picks_observed=len(manager_picks),
        position_counts=position_counts,
        position_preferences=position_preferences,
        risk_tolerance=round(risk_tolerance, 4),
        market_timing=round(market_timing, 4),
    )

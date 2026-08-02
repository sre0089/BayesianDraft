from pydantic import BaseModel

from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import RankingRow


class RecommendationScore(BaseModel):
    player_id: str
    rank: int
    total_score: float
    value_score: float
    need_score: float
    tier_score: float
    market_score: float
    penalty: float
    confidence: float
    next_pick_availability: float
    explanation: list[str]


class RecommendationResult(BaseModel):
    primary: RecommendationScore
    alternatives: list[RecommendationScore]


STARTER_TARGETS = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "DST": 1,
    "K": 1,
}


def recommend_players(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    limit: int = 4,
) -> RecommendationResult:
    available_ids = set(draft_state.available_player_ids)
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    scored = [
        _score_candidate(draft_state, ranking)
        for ranking in rankings
        if ranking.player_id in available_ids
    ]
    scored.sort(key=lambda score: (-score.total_score, ranking_by_id[score.player_id].overall_rank))

    if not scored:
        raise ValueError("no available players to recommend")

    primary = scored[0]
    alternatives = scored[1:limit]
    return RecommendationResult(primary=primary, alternatives=alternatives)


def _score_candidate(draft_state: DraftState, ranking: RankingRow) -> RecommendationScore:
    roster = draft_state.rosters[draft_state.league_config.league.user_manager_id]
    drafted_position_count = roster.positional_counts.get(ranking.position.value, 0)
    target_count = STARTER_TARGETS[ranking.position.value]
    starting_need = max(target_count - drafted_position_count, 0)
    value_score = ranking.vorp
    need_score = starting_need * 35
    tier_score = max(4 - ranking.tier, 0) * 8
    market_score = max(ranking.adp_delta or 0, 0) * 0.5
    penalty = _late_position_penalty(draft_state, ranking, drafted_position_count)
    total_score = value_score + need_score + tier_score + market_score - penalty
    next_pick_availability = _estimate_next_pick_availability(draft_state, ranking)
    confidence = _confidence_from_margin(total_score, value_score)

    return RecommendationScore(
        player_id=ranking.player_id,
        rank=ranking.overall_rank,
        total_score=round(total_score, 3),
        value_score=round(value_score, 3),
        need_score=round(need_score, 3),
        tier_score=round(tier_score, 3),
        market_score=round(market_score, 3),
        penalty=round(penalty, 3),
        confidence=confidence,
        next_pick_availability=next_pick_availability,
        explanation=_explain(
            ranking,
            starting_need=starting_need,
            market_score=market_score,
            penalty=penalty,
            availability=next_pick_availability,
        ),
    )


def _late_position_penalty(
    draft_state: DraftState,
    ranking: RankingRow,
    drafted_position_count: int,
) -> float:
    if ranking.position.value not in {"K", "DST"}:
        return 0
    if drafted_position_count > 0:
        return 80
    return 45 if draft_state.current_round is not None and draft_state.current_round < 14 else 0


def _estimate_next_pick_availability(draft_state: DraftState, ranking: RankingRow) -> float:
    future_picks = draft_state.user_future_picks
    if not future_picks:
        return 0
    picks_until_next_user_pick = max(
        future_picks[0].overall_pick - draft_state.current_overall_pick,
        0,
    )
    adp = ranking.adp or ranking.overall_rank
    scarcity_pressure = max(0, adp - draft_state.current_overall_pick) / max(
        picks_until_next_user_pick,
        1,
    )
    return round(max(0.02, min(0.98, scarcity_pressure / 3)), 3)


def _confidence_from_margin(total_score: float, value_score: float) -> float:
    raw_confidence = 0.45 + min(abs(total_score - value_score) / 120, 0.4)
    return round(raw_confidence, 3)


def _explain(
    ranking: RankingRow,
    *,
    starting_need: int,
    market_score: float,
    penalty: float,
    availability: float,
) -> list[str]:
    explanation = [
        f"Ranks {ranking.overall_rank} overall and {ranking.position_rank} at {ranking.position}.",
        f"Adds {ranking.vorp:.1f} points over replacement.",
    ]
    if starting_need > 0:
        explanation.append(f"Fills a remaining starter need at {ranking.position}.")
    if ranking.tier == 1:
        explanation.append("Still sits in the top tier at the position.")
    if market_score > 0:
        explanation.append(
            f"Market cost is favorable by {ranking.adp_delta:.1f} picks versus rank."
        )
    if penalty > 0:
        explanation.append("Penalty applied for spending early draft capital on K/DST.")
    explanation.append(f"Estimated next-pick availability is {availability:.0%}.")
    return explanation

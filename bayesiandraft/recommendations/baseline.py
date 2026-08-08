from pydantic import BaseModel

from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import RankingRow
from bayesiandraft.recommendations.path_context import PathBankContext


class RecommendationScore(BaseModel):
    player_id: str
    rank: int
    draft_phase: str
    total_score: float
    value_score: float
    need_score: float
    tier_score: float
    tier_drop_score: float
    opportunity_cost_score: float = 0
    market_score: float
    next_pick_risk_score: float
    penalty: float
    confidence: float
    next_pick_availability: float
    explanation: list[str]


class RecommendationResult(BaseModel):
    primary: RecommendationScore
    alternatives: list[RecommendationScore]


class PositionalRecommendationGroup(BaseModel):
    position: str
    remaining_need: int
    candidates: list[RecommendationScore]


DEFAULT_STARTER_TARGETS = {
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
    path_context: PathBankContext | None = None,
    candidate_pool_size: int = 260,
) -> RecommendationResult:
    available_ids = set(draft_state.available_player_ids)
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    tier_counts = _tier_counts(rankings, available_ids)
    candidate_rankings = _candidate_rankings(
        draft_state,
        rankings,
        available_ids,
        candidate_pool_size=candidate_pool_size,
    )
    scored = [
        _score_candidate(
            draft_state,
            ranking,
            rankings,
            path_context=path_context,
            tier_counts=tier_counts,
        )
        for ranking in candidate_rankings
    ]
    scored.sort(key=lambda score: (-score.total_score, ranking_by_id[score.player_id].overall_rank))

    if not scored:
        raise ValueError("no available players to recommend")

    primary = scored[0]
    alternatives = scored[1:limit]
    return RecommendationResult(primary=primary, alternatives=alternatives)


def recommend_players_by_needed_position(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    per_position_limit: int = 5,
    path_context: PathBankContext | None = None,
) -> list[PositionalRecommendationGroup]:
    available_ids = set(draft_state.available_player_ids)
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    needed_positions = _needed_positions(draft_state)
    tier_counts = _tier_counts(rankings, available_ids)
    groups: list[PositionalRecommendationGroup] = []

    for position, remaining_need in needed_positions.items():
        scored = [
            _score_candidate(
                draft_state,
                ranking,
                rankings,
                path_context=path_context,
                tier_counts=tier_counts,
            )
            for ranking in rankings
            if ranking.player_id in available_ids and ranking.position.value == position
        ]
        scored.sort(
            key=lambda score: (-score.total_score, ranking_by_id[score.player_id].overall_rank)
        )
        groups.append(
            PositionalRecommendationGroup(
                position=position,
                remaining_need=remaining_need,
                candidates=scored[:per_position_limit],
            )
        )

    return groups


def _score_candidate(
    draft_state: DraftState,
    ranking: RankingRow,
    rankings: list[RankingRow],
    *,
    path_context: PathBankContext | None = None,
    tier_counts: dict[tuple[str, int], int] | None = None,
) -> RecommendationScore:
    roster = draft_state.rosters[draft_state.league_config.league.user_manager_id]
    drafted_position_count = roster.positional_counts.get(ranking.position.value, 0)
    target_count = _starter_targets(draft_state).get(
        ranking.position.value,
        DEFAULT_STARTER_TARGETS[ranking.position.value],
    )
    base_need = max(target_count - drafted_position_count, 0)
    flex_need = _flex_need_for_position(draft_state, ranking.position.value)
    starting_need = base_need + flex_need
    draft_phase = _draft_phase(draft_state)
    need_weight = _need_weight(draft_phase)
    value_score = ranking.vorp
    need_score = starting_need * 35 * need_weight
    tier_score = max(4 - ranking.tier, 0) * 8
    tier_drop_score = _tier_drop_score(
        draft_state,
        ranking,
        rankings,
        draft_phase,
        tier_counts=tier_counts,
    )
    opportunity_cost_score = _opportunity_cost_score(path_context, ranking)
    market_score = max(ranking.adp_delta or 0, 0) * 0.5
    penalty = _late_position_penalty(draft_state, ranking, drafted_position_count)
    next_pick_availability = _estimate_next_pick_availability(draft_state, ranking)
    next_pick_risk_score = _next_pick_risk_score(next_pick_availability, draft_phase)
    total_score = (
        value_score
        + need_score
        + tier_score
        + tier_drop_score
        + opportunity_cost_score
        + market_score
        + next_pick_risk_score
        - penalty
    )
    confidence = _confidence_from_margin(total_score, value_score)

    return RecommendationScore(
        player_id=ranking.player_id,
        rank=ranking.overall_rank,
        draft_phase=draft_phase,
        total_score=round(total_score, 3),
        value_score=round(value_score, 3),
        need_score=round(need_score, 3),
        tier_score=round(tier_score, 3),
        tier_drop_score=round(tier_drop_score, 3),
        opportunity_cost_score=round(opportunity_cost_score, 3),
        market_score=round(market_score, 3),
        next_pick_risk_score=round(next_pick_risk_score, 3),
        penalty=round(penalty, 3),
        confidence=confidence,
        next_pick_availability=next_pick_availability,
        explanation=_explain(
            ranking,
            starting_need=starting_need,
            base_need=base_need,
            flex_need=flex_need,
            draft_phase=draft_phase,
            need_weight=need_weight,
            tier_drop_score=tier_drop_score,
            opportunity_cost_score=opportunity_cost_score,
            path_context=path_context,
            market_score=market_score,
            next_pick_risk_score=next_pick_risk_score,
            penalty=penalty,
            availability=next_pick_availability,
        ),
    )


def _needed_positions(draft_state: DraftState) -> dict[str, int]:
    roster = draft_state.rosters[draft_state.league_config.league.user_manager_id]
    needs: dict[str, int] = {}
    base_flex_needs = 0
    starter_targets = _starter_targets(draft_state)

    for position, target_count in starter_targets.items():
        remaining = max(target_count - roster.positional_counts.get(position, 0), 0)
        if remaining > 0:
            needs[position] = remaining
        if position in draft_state.league_config.roster.flex_eligibility.get("FLEX", []):
            base_flex_needs += remaining

    flex_slots = draft_state.league_config.roster.starting_slots.get("FLEX", 0)
    if flex_slots <= 0 or base_flex_needs > 0:
        return needs

    flex_positions = set(draft_state.league_config.roster.flex_eligibility.get("FLEX", []))
    flex_roster_count = sum(
        roster.positional_counts.get(position, 0) for position in flex_positions
    )
    base_flex_target = sum(starter_targets.get(position, 0) for position in flex_positions)
    if flex_roster_count < base_flex_target + flex_slots:
        for position in flex_positions:
            needs[position] = max(needs.get(position, 0), 1)

    return needs


def _candidate_rankings(
    draft_state: DraftState,
    rankings: list[RankingRow],
    available_ids: set[str],
    *,
    candidate_pool_size: int,
    per_needed_position: int = 12,
) -> list[RankingRow]:
    candidate_ids: set[str] = set()
    candidates: list[RankingRow] = []
    for ranking in rankings:
        if ranking.player_id not in available_ids:
            continue
        if len(candidates) < candidate_pool_size:
            candidates.append(ranking)
            candidate_ids.add(ranking.player_id)

    needed_positions = _needed_positions(draft_state)
    needed_counts = {position: 0 for position in needed_positions}
    for ranking in rankings:
        position = ranking.position.value
        if position not in needed_counts:
            continue
        if needed_counts[position] >= per_needed_position:
            continue
        if ranking.player_id not in available_ids:
            continue
        needed_counts[position] += 1
        if ranking.player_id in candidate_ids:
            continue
        candidates.append(ranking)
        candidate_ids.add(ranking.player_id)
    return candidates


def _starter_targets(draft_state: DraftState) -> dict[str, int]:
    flex_slot_names = set(draft_state.league_config.roster.flex_eligibility)
    return {
        position: count
        for position, count in draft_state.league_config.roster.starting_slots.items()
        if position not in flex_slot_names
    }


def _flex_need_for_position(draft_state: DraftState, position: str) -> int:
    roster = draft_state.rosters[draft_state.league_config.league.user_manager_id]
    starter_targets = _starter_targets(draft_state)
    flex_need = 0
    for flex_slot, eligible_positions in draft_state.league_config.roster.flex_eligibility.items():
        if position not in eligible_positions:
            continue
        base_needs = sum(
            max(
                starter_targets.get(eligible_position, 0)
                - roster.positional_counts.get(eligible_position, 0),
                0,
            )
            for eligible_position in eligible_positions
        )
        if base_needs > 0:
            continue
        flex_slots = draft_state.league_config.roster.starting_slots.get(flex_slot, 0)
        eligible_count = sum(
            roster.positional_counts.get(eligible_position, 0)
            for eligible_position in eligible_positions
        )
        base_target = sum(
            starter_targets.get(eligible_position, 0)
            for eligible_position in eligible_positions
        )
        flex_need += max(base_target + flex_slots - eligible_count, 0)
    return flex_need


def _opportunity_cost_score(
    path_context: PathBankContext | None,
    ranking: RankingRow,
) -> float:
    if path_context is None:
        return 0
    estimate = path_context.opportunity_for(ranking.position.value)
    if estimate is None:
        return 0
    return min(estimate.opportunity_cost * 0.35, 35)


def _tier_counts(
    rankings: list[RankingRow],
    available_ids: set[str],
) -> dict[tuple[str, int], int]:
    counts: dict[tuple[str, int], int] = {}
    for ranking in rankings:
        if ranking.player_id not in available_ids:
            continue
        key = (ranking.position.value, ranking.tier)
        counts[key] = counts.get(key, 0) + 1
    return counts


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


def _draft_phase(draft_state: DraftState) -> str:
    round_number = draft_state.current_round or 1
    if round_number <= 4:
        return "early"
    if round_number <= 10:
        return "middle"
    return "late"


def _need_weight(draft_phase: str) -> float:
    return {
        "early": 0.35,
        "middle": 0.8,
        "late": 1.2,
    }[draft_phase]


def _tier_drop_score(
    draft_state: DraftState,
    ranking: RankingRow,
    rankings: list[RankingRow],
    draft_phase: str,
    *,
    tier_counts: dict[tuple[str, int], int] | None = None,
) -> float:
    if tier_counts is None:
        tier_counts = _tier_counts(rankings, set(draft_state.available_player_ids))
    same_position_tier_count = tier_counts.get((ranking.position.value, ranking.tier), 0)
    if same_position_tier_count > 3:
        return 0

    phase_multiplier = {
        "early": 1.2,
        "middle": 1.0,
        "late": 0.6,
    }[draft_phase]
    tier_quality = max(4 - ranking.tier, 0)
    scarcity = max(4 - same_position_tier_count, 0)
    return scarcity * tier_quality * 4 * phase_multiplier


def _next_pick_risk_score(availability: float, draft_phase: str) -> float:
    phase_multiplier = {
        "early": 1.1,
        "middle": 1.0,
        "late": 0.7,
    }[draft_phase]
    return (1 - availability) * 18 * phase_multiplier


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
    base_need: int,
    flex_need: int,
    draft_phase: str,
    need_weight: float,
    tier_drop_score: float,
    opportunity_cost_score: float,
    path_context: PathBankContext | None,
    market_score: float,
    next_pick_risk_score: float,
    penalty: float,
    availability: float,
) -> list[str]:
    explanation = [
        f"Draft phase is {draft_phase}; roster need weight is {need_weight:.0%}.",
        f"Ranks {ranking.overall_rank} overall and {ranking.position_rank} at {ranking.position}.",
        f"Adds {ranking.vorp:.1f} points over replacement.",
    ]
    if starting_need > 0:
        if base_need > 0:
            explanation.append(f"Fills a remaining starter need at {ranking.position}.")
        elif flex_need > 0:
            explanation.append(f"Fills a remaining FLEX need with {ranking.position}.")
    if ranking.tier == 1:
        explanation.append("Still sits in the top tier at the position.")
    if tier_drop_score > 0:
        explanation.append("Gets a tier-drop boost because similar options are thinning.")
    if opportunity_cost_score > 0 and path_context is not None:
        estimate = path_context.opportunity_for(ranking.position.value)
        if estimate is not None and estimate.expected_later_player_name is not None:
            explanation.append(
                "Gets an opportunity-cost boost because the expected later "
                f"{ranking.position} is {estimate.expected_later_player_name}."
            )
        else:
            explanation.append("Gets an opportunity-cost boost from the path bank.")
    if market_score > 0:
        explanation.append(
            f"Market cost is favorable by {ranking.adp_delta:.1f} picks versus rank."
        )
    if next_pick_risk_score > 0:
        explanation.append("Gets a next-pick risk boost because it may not come back.")
    if penalty > 0:
        explanation.append("Penalty applied for spending early draft capital on K/DST.")
    explanation.append(f"Estimated next-pick availability is {availability:.0%}.")
    return explanation

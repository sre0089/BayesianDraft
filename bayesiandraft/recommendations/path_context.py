from pydantic import BaseModel

from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import RankingRow
from bayesiandraft.simulation import DraftPath, DraftPathBank


class OpportunityCostEstimate(BaseModel):
    position: str
    current_vorp: float
    expected_later_vorp: float
    opportunity_cost: float
    expected_later_player_id: str | None = None
    expected_later_player_name: str | None = None


class PathBankContext(BaseModel):
    exact_match_count: int
    similar_path_count: int
    sample_quality: str
    next_user_pick: int | None
    opportunity_by_position: dict[str, OpportunityCostEstimate]

    def opportunity_for(self, position: str) -> OpportunityCostEstimate | None:
        return self.opportunity_by_position.get(position)


def build_path_bank_context(
    draft_state: DraftState,
    rankings: list[RankingRow],
    path_bank: DraftPathBank,
) -> PathBankContext:
    next_user_pick = (
        draft_state.user_future_picks[0].overall_pick if draft_state.user_future_picks else None
    )
    if next_user_pick is None:
        return PathBankContext(
            exact_match_count=0,
            similar_path_count=0,
            sample_quality="no_future_pick",
            next_user_pick=None,
            opportunity_by_position={},
        )

    exact_paths = _exact_prefix_paths(draft_state, path_bank.paths)
    similar_paths = exact_paths or _compatible_paths(draft_state, path_bank.paths)
    sample_quality = _sample_quality(
        exact_count=len(exact_paths),
        similar_count=len(similar_paths),
        total_count=len(path_bank.paths),
    )
    if not similar_paths:
        similar_paths = path_bank.paths
        sample_quality = "fallback"

    return PathBankContext(
        exact_match_count=len(exact_paths),
        similar_path_count=len(similar_paths),
        sample_quality=sample_quality,
        next_user_pick=next_user_pick,
        opportunity_by_position=_opportunity_by_position(
            draft_state,
            rankings,
            similar_paths,
            next_user_pick=next_user_pick,
        ),
    )


def _exact_prefix_paths(draft_state: DraftState, paths: list[DraftPath]) -> list[DraftPath]:
    real_picks = draft_state.completed_picks
    if not real_picks:
        return paths
    exact_paths = []
    for path in paths:
        if len(path.picks) < len(real_picks):
            continue
        if all(
            path.picks[index].player_id == pick.player_id
            for index, pick in enumerate(real_picks)
        ):
            exact_paths.append(path)
    return exact_paths


def _compatible_paths(draft_state: DraftState, paths: list[DraftPath]) -> list[DraftPath]:
    real_drafted_ids = {pick.player_id for pick in draft_state.completed_picks}
    current_pick = draft_state.current_overall_pick
    compatible = []
    for path in paths:
        path_drafted_before_now = {
            pick.player_id for pick in path.picks if pick.overall_pick < current_pick
        }
        if real_drafted_ids <= path_drafted_before_now:
            compatible.append(path)
    return compatible


def _sample_quality(*, exact_count: int, similar_count: int, total_count: int) -> str:
    if exact_count > 0:
        return "exact"
    if total_count == 0:
        return "empty"
    share = similar_count / total_count
    if share >= 0.25:
        return "strong"
    if share >= 0.05:
        return "thin"
    return "fallback"


def _opportunity_by_position(
    draft_state: DraftState,
    rankings: list[RankingRow],
    paths: list[DraftPath],
    *,
    next_user_pick: int,
) -> dict[str, OpportunityCostEstimate]:
    available_ids = set(draft_state.available_player_ids)
    top_now_by_position = _top_available_by_position(rankings, available_ids)
    later_values_by_position: dict[str, list[tuple[float, str]]] = {
        position: [] for position in top_now_by_position
    }

    for path in paths:
        path_drafted_before_next = {
            pick.player_id for pick in path.picks if pick.overall_pick < next_user_pick
        }
        path_available = available_ids - path_drafted_before_next
        top_later = _top_available_by_position(rankings, path_available)
        for position in top_now_by_position:
            later = top_later.get(position)
            if later is not None:
                later_values_by_position[position].append((later.vorp, later.player_id))

    estimates = {}
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    for position, current in top_now_by_position.items():
        later_values = later_values_by_position.get(position, [])
        expected_later_vorp = _mean([value for value, _player_id in later_values])
        expected_later_player_id = _most_common_player_id(later_values)
        expected_later_player_name = (
            ranking_by_id[expected_later_player_id].full_name
            if expected_later_player_id in ranking_by_id
            else None
        )
        estimates[position] = OpportunityCostEstimate(
            position=position,
            current_vorp=round(current.vorp, 4),
            expected_later_vorp=round(expected_later_vorp, 4),
            opportunity_cost=round(max(current.vorp - expected_later_vorp, 0), 4),
            expected_later_player_id=expected_later_player_id,
            expected_later_player_name=expected_later_player_name,
        )
    return estimates


def _top_available_by_position(
    rankings: list[RankingRow],
    available_ids: set[str],
) -> dict[str, RankingRow]:
    top: dict[str, RankingRow] = {}
    for ranking in rankings:
        position = ranking.position.value
        if ranking.player_id in available_ids and position not in top:
            top[position] = ranking
    return top


def _most_common_player_id(values: list[tuple[float, str]]) -> str | None:
    if not values:
        return None
    counts: dict[str, int] = {}
    for _value, player_id in values:
        counts[player_id] = counts.get(player_id, 0) + 1
    return max(counts, key=lambda player_id: (counts[player_id], player_id))


def _mean(values: list[float]) -> float:
    if not values:
        return 0
    return sum(values) / len(values)

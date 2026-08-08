from pydantic import BaseModel

from bayesiandraft.config import LeagueConfig
from bayesiandraft.rankings import RankingRow


class RosterStrengthScore(BaseModel):
    projected_points: float
    vorp: float
    starter_projected_points: float
    starter_vorp: float
    bench_projected_points: float
    bench_vorp: float
    starter_player_ids: list[str]
    bench_player_ids: list[str]


def score_roster_strength(
    player_ids: list[str],
    *,
    rankings: dict[str, RankingRow],
    league_config: LeagueConfig,
    bench_discount: float = 0.15,
) -> RosterStrengthScore:
    available_rows = [rankings[player_id] for player_id in player_ids if player_id in rankings]
    starters: list[RankingRow] = []

    for position, slot_count in league_config.roster.starting_slots.items():
        if position == "FLEX":
            continue
        selected = _take_best_at_position(available_rows, position, slot_count)
        starters.extend(selected)

    for flex_position, slot_count in league_config.roster.starting_slots.items():
        if flex_position != "FLEX":
            continue
        eligible_positions = set(league_config.roster.flex_eligibility.get(flex_position, []))
        selected = _take_best_flex(available_rows, eligible_positions, slot_count)
        starters.extend(selected)

    starter_ids = {row.player_id for row in starters}
    bench = [row for row in available_rows if row.player_id not in starter_ids]
    starter_points = sum(row.projected_points for row in starters)
    starter_vorp = sum(row.vorp for row in starters)
    bench_points = sum(row.projected_points for row in bench)
    bench_vorp = sum(max(row.vorp, 0) for row in bench)

    return RosterStrengthScore(
        projected_points=round(starter_points + bench_points * bench_discount, 4),
        vorp=round(starter_vorp + bench_vorp * bench_discount, 4),
        starter_projected_points=round(starter_points, 4),
        starter_vorp=round(starter_vorp, 4),
        bench_projected_points=round(bench_points * bench_discount, 4),
        bench_vorp=round(bench_vorp * bench_discount, 4),
        starter_player_ids=[row.player_id for row in starters],
        bench_player_ids=[row.player_id for row in bench],
    )


def _take_best_at_position(
    available_rows: list[RankingRow],
    position: str,
    count: int,
) -> list[RankingRow]:
    selected = [
        row for row in sorted(available_rows, key=lambda row: (-row.vorp, -row.projected_points))
        if row.position.value == position
    ][:count]
    _remove_selected(available_rows, selected)
    return selected


def _take_best_flex(
    available_rows: list[RankingRow],
    eligible_positions: set[str],
    count: int,
) -> list[RankingRow]:
    selected = [
        row for row in sorted(available_rows, key=lambda row: (-row.vorp, -row.projected_points))
        if row.position.value in eligible_positions
    ][:count]
    _remove_selected(available_rows, selected)
    return selected


def _remove_selected(available_rows: list[RankingRow], selected: list[RankingRow]) -> None:
    selected_ids = {row.player_id for row in selected}
    available_rows[:] = [row for row in available_rows if row.player_id not in selected_ids]

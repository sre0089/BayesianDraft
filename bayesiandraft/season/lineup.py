from collections.abc import Callable

from pydantic import BaseModel

from bayesiandraft.config import LeagueConfig
from bayesiandraft.domain import Position


class WeeklyPlayerScore(BaseModel):
    player_id: str
    position: Position
    points: float


class LineupSlot(BaseModel):
    slot: str
    player_id: str
    position: Position
    points: float


class OptimizedLineup(BaseModel):
    starters: list[LineupSlot]
    bench: list[WeeklyPlayerScore]
    total_points: float
    open_slots: dict[str, int]


def optimize_lineup(
    players: list[WeeklyPlayerScore],
    league_config: LeagueConfig,
) -> OptimizedLineup:
    remaining = sorted(players, key=lambda player: player.points, reverse=True)
    starters: list[LineupSlot] = []
    open_slots: dict[str, int] = {}

    for slot, count in league_config.roster.starting_slots.items():
        if slot in league_config.roster.flex_eligibility:
            continue
        selected = _take_position(remaining, slot, count)
        starters.extend(
            LineupSlot(
                slot=slot,
                player_id=player.player_id,
                position=player.position,
                points=player.points,
            )
            for player in selected
        )
        if len(selected) < count:
            open_slots[slot] = count - len(selected)

    for slot, count in league_config.roster.starting_slots.items():
        eligible_positions = league_config.roster.flex_eligibility.get(slot)
        if eligible_positions is None:
            continue
        selected = _take_flex(remaining, eligible_positions, count)
        starters.extend(
            LineupSlot(
                slot=slot,
                player_id=player.player_id,
                position=player.position,
                points=player.points,
            )
            for player in selected
        )
        if len(selected) < count:
            open_slots[slot] = count - len(selected)

    return OptimizedLineup(
        starters=starters,
        bench=remaining,
        total_points=round(sum(player.points for player in starters), 4),
        open_slots=open_slots,
    )


def _take_position(
    remaining: list[WeeklyPlayerScore],
    position: str,
    count: int,
) -> list[WeeklyPlayerScore]:
    return _take_matching(
        remaining,
        count,
        lambda player: player.position.value == position,
    )


def _take_flex(
    remaining: list[WeeklyPlayerScore],
    eligible_positions: list[str],
    count: int,
) -> list[WeeklyPlayerScore]:
    eligible = set(eligible_positions)
    return _take_matching(
        remaining,
        count,
        lambda player: player.position.value in eligible,
    )


def _take_matching(
    remaining: list[WeeklyPlayerScore],
    count: int,
    predicate: Callable[[WeeklyPlayerScore], bool],
) -> list[WeeklyPlayerScore]:
    selected: list[WeeklyPlayerScore] = []
    for player in list(remaining):
        if len(selected) >= count:
            break
        if predicate(player):
            selected.append(player)
            remaining.remove(player)
    return selected

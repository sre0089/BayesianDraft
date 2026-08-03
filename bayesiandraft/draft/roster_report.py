from pydantic import BaseModel

from bayesiandraft.draft.state import DraftState


class PositionBalance(BaseModel):
    position: str
    current_count: int
    starter_target: int
    remaining_starter_need: int
    surplus: int


class RosterBalanceReport(BaseModel):
    manager_id: str
    roster_size: int
    positions: list[PositionBalance]


def build_roster_balance_report(state: DraftState, manager_id: str) -> RosterBalanceReport:
    roster = state.rosters[manager_id]
    positions = []
    for position, starter_target in sorted(state.league_config.roster.starting_slots.items()):
        if position in state.league_config.roster.flex_eligibility:
            continue
        current_count = roster.positional_counts.get(position, 0)
        positions.append(
            PositionBalance(
                position=position,
                current_count=current_count,
                starter_target=starter_target,
                remaining_starter_need=max(starter_target - current_count, 0),
                surplus=max(current_count - starter_target, 0),
            )
        )
    return RosterBalanceReport(
        manager_id=manager_id,
        roster_size=len(roster.player_ids),
        positions=positions,
    )

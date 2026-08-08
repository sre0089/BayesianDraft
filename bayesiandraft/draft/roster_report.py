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
    base_targets = {
        position: starter_target
        for position, starter_target in state.league_config.roster.starting_slots.items()
        if position not in state.league_config.roster.flex_eligibility
    }
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
    for flex_position, starter_target in sorted(
        state.league_config.roster.starting_slots.items()
    ):
        eligible_positions = state.league_config.roster.flex_eligibility.get(flex_position)
        if eligible_positions is None:
            continue
        eligible_count = sum(
            roster.positional_counts.get(position, 0) for position in eligible_positions
        )
        base_target = sum(base_targets.get(position, 0) for position in eligible_positions)
        current_count = max(eligible_count - base_target, 0)
        positions.append(
            PositionBalance(
                position=flex_position,
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

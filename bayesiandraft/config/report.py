from pydantic import BaseModel

from bayesiandraft.config.league import LeagueConfig
from bayesiandraft.draft import default_total_rounds


class LeagueSanityReport(BaseModel):
    platform: str
    season: int
    team_count: int
    user_manager_id: str
    user_draft_position: int
    draft_order_count: int
    total_rounds: int
    total_picks: int
    starting_slot_count: int
    bench_slots: int
    warnings: list[str]


def build_league_sanity_report(config: LeagueConfig) -> LeagueSanityReport:
    total_rounds = default_total_rounds(config)
    warnings = []
    if config.league.team_count != len(config.draft_order):
        warnings.append("Team count does not match draft order length.")
    if config.roster.ir_slots > 0:
        warnings.append("IR slots are excluded from draft length.")

    return LeagueSanityReport(
        platform=config.platform,
        season=config.season,
        team_count=config.league.team_count,
        user_manager_id=config.league.user_manager_id,
        user_draft_position=config.league.user_draft_position,
        draft_order_count=len(config.draft_order),
        total_rounds=total_rounds,
        total_picks=total_rounds * config.league.team_count,
        starting_slot_count=sum(config.roster.starting_slots.values()),
        bench_slots=config.roster.bench_slots,
        warnings=warnings,
    )

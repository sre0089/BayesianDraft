from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import DraftState, Player, build_roster_balance_report


def test_roster_balance_reports_starter_needs() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    players = [
        Player(
            player_id=player.player_id,
            full_name=player.full_name,
            position=player.position.value,
            nfl_team_id=player.nfl_team_id,
        )
        for player in snapshot.players
    ]
    state = DraftState.create(load_league_config("configs/leagues/espn_2026.yaml"), players)

    report = build_roster_balance_report(state, "user_manager")

    assert report.roster_size == 0
    assert {position.position for position in report.positions} == {
        "DST",
        "FLEX",
        "K",
        "QB",
        "RB",
        "TE",
        "WR",
    }
    rb_balance = next(position for position in report.positions if position.position == "RB")
    assert rb_balance.remaining_starter_need == 2
    flex_balance = next(position for position in report.positions if position.position == "FLEX")
    assert flex_balance.remaining_starter_need == 1


def test_roster_balance_counts_extra_eligible_players_toward_flex() -> None:
    snapshot = load_player_snapshot(Path("data/fixtures/baseline_players_2026.json"))
    players = [
        Player(
            player_id=player.player_id,
            full_name=player.full_name,
            position=player.position.value,
            nfl_team_id=player.nfl_team_id,
        )
        for player in snapshot.players
    ]
    state = DraftState.create(load_league_config("configs/leagues/espn_2026.yaml"), players)
    state.rosters["user_manager"].positional_counts = {"RB": 2, "WR": 3, "TE": 1}

    report = build_roster_balance_report(state, "user_manager")

    flex_balance = next(position for position in report.positions if position.position == "FLEX")
    assert flex_balance.current_count == 1
    assert flex_balance.remaining_starter_need == 0

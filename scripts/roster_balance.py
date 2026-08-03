from argparse import ArgumentParser
from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import (
    DraftState,
    Player,
    apply_rehearsal_scenario,
    build_roster_balance_report,
    load_rehearsal_scenario,
)


def main() -> None:
    parser = ArgumentParser(description="Print a roster balance report.")
    parser.add_argument("--manager-id", default="user_manager")
    parser.add_argument("--scenario", default="data/fixtures/rehearsal_user_pick_8.json")
    args = parser.parse_args()

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
    state = apply_rehearsal_scenario(state, load_rehearsal_scenario(args.scenario))
    print(build_roster_balance_report(state, args.manager_id).model_dump_json(indent=2))


if __name__ == "__main__":
    main()

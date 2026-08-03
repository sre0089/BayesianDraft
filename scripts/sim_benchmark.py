from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import DraftState, Player
from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import benchmark_remaining_draft


def main() -> None:
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
    result = benchmark_remaining_draft(state, build_baseline_rankings(snapshot))
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

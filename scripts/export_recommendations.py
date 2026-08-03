from argparse import ArgumentParser
from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import (
    DraftState,
    Player,
    apply_rehearsal_scenario,
    load_rehearsal_scenario,
)
from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.recommendations import recommend_players


def main() -> None:
    parser = ArgumentParser(description="Export BayesianDraft baseline recommendations.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--scenario")
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
    if args.scenario:
        state = apply_rehearsal_scenario(state, load_rehearsal_scenario(args.scenario))

    recommendations = recommend_players(state, build_baseline_rankings(snapshot))
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(recommendations.model_dump_json(indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

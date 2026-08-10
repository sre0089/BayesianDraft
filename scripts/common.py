from argparse import ArgumentParser
from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import PlayerSnapshot, load_player_snapshot
from bayesiandraft.draft import DraftState, Player

DEFAULT_LEAGUE_CONFIG_PATH = Path("configs/leagues/espn_2026.yaml")
DEFAULT_LOCAL_LEAGUE_CONFIG_PATH = Path("configs/leagues/espn_2026.local.yaml")
DEFAULT_PLAYER_SNAPSHOT_PATH = Path("data/fixtures/baseline_players_2026.json")


def add_snapshot_argument(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--snapshot",
        default=str(DEFAULT_PLAYER_SNAPSHOT_PATH),
        help="Path to a validated player snapshot JSON file.",
    )


def add_league_config_argument(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--league-config",
        default=str(default_cli_league_config_path()),
        help="Path to a league config YAML file.",
    )


def default_cli_league_config_path() -> Path:
    if DEFAULT_LOCAL_LEAGUE_CONFIG_PATH.exists():
        return DEFAULT_LOCAL_LEAGUE_CONFIG_PATH
    return DEFAULT_LEAGUE_CONFIG_PATH


def load_snapshot_and_draft_state(
    snapshot_path: str | Path = DEFAULT_PLAYER_SNAPSHOT_PATH,
    league_config_path: str | Path = DEFAULT_LEAGUE_CONFIG_PATH,
) -> tuple[PlayerSnapshot, DraftState]:
    snapshot = load_player_snapshot(snapshot_path)
    players = [
        Player(
            player_id=player.player_id,
            full_name=player.full_name,
            position=player.position.value,
            nfl_team_id=player.nfl_team_id,
        )
        for player in snapshot.players
    ]
    state = DraftState.create(load_league_config(league_config_path), players)
    return snapshot, state

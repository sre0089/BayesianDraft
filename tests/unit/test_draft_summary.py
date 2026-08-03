from pathlib import Path

from bayesiandraft.config import load_league_config
from bayesiandraft.data import load_player_snapshot
from bayesiandraft.draft import DraftState, Player, summarize_draft_state


def test_draft_summary_counts_initial_state() -> None:
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

    summary = summarize_draft_state(state)

    assert summary.current_overall_pick == 1
    assert summary.completed_pick_count == 0
    assert summary.available_player_count == 12
    assert summary.next_user_pick == 8

from pathlib import Path

from bayesiandraft.cli import CliDraftConfig, CliDraftController
from scripts.common import load_snapshot_and_draft_state


def test_cli_controller_renders_summary_and_rankings(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )

    assert controller.current_view == "Summary"
    assert any("Current pick: 1" in line for line in controller.view_lines())

    controller.move_view(1)

    assert controller.current_view == "Rankings"
    assert controller.view_lines()[0].startswith(">")


def test_cli_controller_filters_and_drafts_selected_player(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )

    controller.move_view(1)
    controller.set_search("Example RB One")
    controller.draft_selected_player()

    assert controller.state.current_overall_pick == 2
    assert controller.state.completed_picks[0].player_id == "rb_001"
    assert "Drafted Example RB One" in controller.status_message


def test_cli_controller_supports_undo_redo_and_save(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    save_path = tmp_path / "draft.json"
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=save_path),
    )

    controller.draft_selected_player()
    controller.undo()
    controller.redo()
    controller.save()

    assert controller.state.current_overall_pick == 2
    assert save_path.exists()
    assert "Saved draft" in controller.status_message


def test_cli_controller_loads_scenario(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(
            save_path=tmp_path / "draft.json",
            scenario_path=Path("data/fixtures/rehearsal_user_pick_8.json"),
        ),
    )

    assert controller.state.current_overall_pick == 8
    assert controller.state.manager_on_clock == "user_manager"
    assert "Loaded scenario" in controller.status_message


def test_cli_controller_renders_recommendations_roster_health_and_picks(
    tmp_path: Path,
) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )
    controller.draft_selected_player()

    controller.view_index = 2
    assert any("Primary recommendation" in line for line in controller.view_lines())

    controller.view_index = 3
    assert any("Roster balance" in line for line in controller.view_lines())

    controller.view_index = 4
    assert any("Snapshot:" in line for line in controller.view_lines())

    controller.view_index = 6
    assert any("manager_01" in line for line in controller.view_lines())

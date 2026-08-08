from pathlib import Path

from bayesiandraft.cli import CliDraftConfig, CliDraftController
from bayesiandraft.cli.tui import _footer_prompt, _handle_live_search_key, _progress_bar
from scripts.common import load_snapshot_and_draft_state


def test_cli_controller_renders_summary_and_rankings(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )

    assert controller.current_view == "Summary"
    assert any("Version" in line for line in controller.view_lines())
    assert "CURRENT PICK" in controller.view_lines()
    assert any(line.startswith(">>> 1/") for line in controller.view_lines())
    assert any("Live entry:" in line for line in controller.view_lines())
    assert any("| __ )" in line for line in controller.view_lines())
    assert any("Best overall recommendation" in line for line in controller.view_lines())
    assert any(line.startswith("Best overall:") for line in controller.view_lines())

    controller.move_view(1)

    assert controller.current_view == "Rankings"
    assert controller.view_lines()[0].startswith("Filters:")
    assert any(
        "Rank" in line and "Player" in line and "VORP" in line
        for line in controller.view_lines()
    )
    assert any(line.startswith(">") for line in controller.view_lines())
    assert not any(line.startswith(">") and "proj=" in line for line in controller.view_lines())
    assert any("Confirm pick 1:" in line for line in controller.view_lines())
    assert any("Selected:" in line for line in controller.view_lines())
    assert any("Projection: mean=" in line for line in controller.view_lines())


def test_cli_summary_recommendation_updates_after_pick(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )

    before = next(
        line for line in controller.view_lines() if line.startswith("Best overall:")
    )

    controller.draft_selected_player()

    after = next(line for line in controller.view_lines() if line.startswith("Best overall:"))
    assert before != after
    assert "Example RB One" not in after


def test_cli_product_prompt_helpers(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )
    controller.set_search("rb")

    assert _progress_bar(10, 20, 12) == "[######......]"
    assert "~/BayesianDraft" in _footer_prompt(controller)
    assert "mode=summary" in _footer_prompt(controller)
    assert "filter=rb" in _footer_prompt(controller)
    assert "pos=ALL" in _footer_prompt(controller)


def test_cli_controller_live_search_filters_without_enter(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )

    controller.start_search()
    _handle_live_search_key(controller, ord("r"))
    _handle_live_search_key(controller, ord("B"))

    assert controller.search_active is True
    assert controller.search_query == "rB"
    assert "mode=SEARCH" in _footer_prompt(controller)
    assert {ranking.position.value for ranking in controller.selectable_rankings()} == {"RB"}

    _handle_live_search_key(controller, 127)

    assert controller.search_query == "r"

    _handle_live_search_key(controller, ord("\n"))

    assert controller.search_active is False


def test_cli_controller_filters_and_drafts_selected_player(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    save_path = tmp_path / "draft.json"
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=save_path),
    )

    controller.move_view(1)
    controller.set_search("Example RB One")
    controller.draft_selected_player()

    assert controller.state.current_overall_pick == 2
    assert controller.state.completed_picks[0].player_id == "rb_001"
    assert "Drafted Example RB One" in controller.status_message
    assert "Autosaved" in controller.status_message
    assert save_path.exists()


def test_cli_controller_filters_rankings_by_position(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )

    assert {ranking.position.value for ranking in controller.selectable_rankings()} > {"RB"}

    controller.set_position_filter("WR")

    assert controller.position_filter == "WR"
    assert {ranking.position.value for ranking in controller.selectable_rankings()} == {"WR"}
    assert any("position=WR" in line for line in controller._ranking_lines())

    controller.cycle_position_filter(1)

    assert controller.position_filter == "TE"


def test_cli_rankings_scroll_with_selection(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )
    controller.move_view(1)

    for _ in range(7):
        controller.move_selection(1)

    visible_rows = controller._visible_rankings(visible_count=5)

    assert controller.selection_index == 7
    assert controller.ranking_scroll_offset > 0
    assert any(index == controller.selection_index for index, _ in visible_rows)


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


def test_cli_controller_can_disable_autosave(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    save_path = tmp_path / "draft.json"
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=save_path, autosave=False),
    )

    controller.draft_selected_player()

    assert not save_path.exists()
    assert "Autosave off." in controller.status_message


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


def test_cli_controller_auto_picks_to_user(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(
            save_path=tmp_path / "draft.json",
            auto_pick_to_user=True,
        ),
    )

    assert controller.state.current_overall_pick == 8
    assert controller.state.manager_on_clock == "user_manager"
    assert len(controller.state.completed_picks) == 7
    assert "Auto-drafted 7 picks" in controller.status_message


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
    recommendation_lines = controller.view_lines()
    assert recommendation_lines[0] == "Top 5 by positions you still need"
    assert any("Best overall recommendation" in line for line in recommendation_lines)
    assert any("RB need=" in line for line in recommendation_lines)
    assert any("WR need=" in line for line in recommendation_lines)
    assert not any("conf=" in line for line in recommendation_lines)

    controller.view_index = 3
    assert any("Managers" in line for line in controller.view_lines())
    assert any("Your Team" in line for line in controller.view_lines())

    controller.move_selection(-1)
    assert controller.manager_selection_index == 6

    controller.view_index = 4
    assert any("Roster balance" in line for line in controller.view_lines())

    controller.view_index = 5
    assert any("Snapshot:" in line for line in controller.view_lines())

    controller.view_index = 7
    assert any("manager_01" in line for line in controller.view_lines())

from pathlib import Path

from bayesiandraft.audit import load_decision_audit
from bayesiandraft.cli import CliDraftConfig, CliDraftController
from bayesiandraft.cli.tui import (
    _footer_prompt,
    _handle_live_search_key,
    _is_quick_search_key,
    _progress_bar,
)
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
    assert "Draft Assistant" in controller.view_lines()
    assert any("Current recommendation:" in line for line in controller.view_lines())
    assert any("Quick direction:" in line for line in controller.view_lines())
    assert any("Deep sim: run Simulation" in line for line in controller.view_lines())
    assert any(line.startswith("Best overall:") for line in controller.view_lines())
    assert any(line.startswith("Breakdown:") for line in controller.view_lines())
    assert any("drop" in line and "risk" in line for line in controller.view_lines())
    assert any("Path analysis:" in line for line in controller.view_lines())

    controller.move_view(1)

    assert controller.current_view == "Rankings"
    assert controller.view_lines()[0].startswith("Filters:")
    assert any(
        "Rank" in line and "Player" in line and "VORP" in line and "ADPΔ" in line
        for line in controller.view_lines()
    )
    assert any("Example RB One" in line and "+4.0" in line for line in controller.view_lines())
    assert any(line.startswith(">") for line in controller.view_lines())
    assert not any(line.startswith(">") and "proj=" in line for line in controller.view_lines())
    assert any("Confirm pick 1:" in line for line in controller.view_lines())
    assert any("Selected:" in line for line in controller.view_lines())
    assert any("Projection: mean=" in line for line in controller.view_lines())


def test_cli_wide_summary_decision_panel_shows_quick_direction(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )

    lines = controller.summary_decision_lines()

    assert "Draft Assistant" in lines
    assert any("Quick direction:" in line for line in lines)
    assert any("Deep sim: run Simulation" in line for line in lines)


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
    assert any("Recommendation" in line for line in controller.view_lines())


def test_cli_draft_assistant_uses_strategy_analysis(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(
            save_path=tmp_path / "draft.json",
            scenario_path=Path("data/fixtures/rehearsal_user_pick_8.json"),
        ),
    )

    controller.run_path_analysis()

    lines = controller.view_lines()

    assert any("Quick direction:" in line for line in lines)
    assert any("Best next-pick direction:" in line for line in lines)
    assert any("Avoid unless value falls:" in line for line in lines)


def test_cli_marks_simulation_stale_after_board_changes(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(
            save_path=tmp_path / "draft.json",
            scenario_path=Path("data/fixtures/rehearsal_user_pick_8.json"),
        ),
    )
    controller.view_index = 6
    controller.run_path_analysis()

    assert any(
        line.startswith("After 40 simulated draft paths:")
        for line in controller.view_lines()
    )

    controller.draft_selected_player()

    lines = controller.view_lines()
    assert "Multi-path draft analysis" in lines
    assert any("Simulation stale:" in line for line in lines)
    controller.view_index = 0
    assert any("Quick direction:" in line for line in controller.view_lines())
    assert any("Deep sim: stale" in line for line in controller.view_lines())


def test_cli_managers_show_team_strength_scores(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )

    controller.draft_selected_player()
    controller.view_index = 3
    controller.manager_selection_index = 0

    lines = controller.view_lines()

    assert any("Proj" in line and "VORP" in line for line in lines)
    assert any("Team 01" in line and "285.0" in line and "100.0" in line for line in lines)
    assert "Team totals: projected=285.0 VORP=100.0" in lines
    assert any("Example RB One" in line and "proj=" in line and "vorp=" in line for line in lines)


def test_cli_summary_does_not_auto_run_rollout_when_user_is_on_clock(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(
            save_path=tmp_path / "draft.json",
            scenario_path=Path("data/fixtures/rehearsal_user_pick_8.json"),
        ),
    )

    assert controller.state.manager_on_clock == "user_manager"
    assert any("Path analysis: run Simulation with a" in line for line in controller.view_lines())
    assert not any("Rollout: avg VORP" in line for line in controller.view_lines())


def test_cli_summary_stays_light_at_later_user_pick(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state(
        "data/processed/dynastyprocess_rankings_2026.json"
    )
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json", auto_pick_to_user=True),
    )
    while controller.state.current_overall_pick < 21:
        controller.draft_selected_player()

    assert controller.state.manager_on_clock == "user_manager"

    lines = controller.view_lines()

    assert any("Path analysis: run Simulation with a" in line for line in lines)
    assert not any("Rollout: avg VORP" in line for line in lines)


def test_cli_simulation_tab_shows_path_analysis(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(
            save_path=tmp_path / "draft.json",
            scenario_path=Path("data/fixtures/rehearsal_user_pick_8.json"),
        ),
    )
    controller.view_index = 6

    lines = controller.view_lines()

    assert "Multi-path draft analysis" in lines
    assert any("Press a to run" in line for line in lines)
    assert "a analyze" in _footer_prompt(controller)

    progress_events = []
    strategy_progress_events = []
    controller.run_path_analysis(
        progress_callback=progress_events.append,
        strategy_progress_callback=strategy_progress_events.append,
    )
    lines = controller.view_lines()

    assert any(line.startswith("After 40 simulated draft paths:") for line in lines)
    assert "Manager Results (ranked by avg finish)" in lines
    assert "Draft Strategy Analysis" in lines
    assert any(
        "Next pick" in line and "avg VORP" in line and "target" in line
        for line in lines
    )
    assert "Risk" in lines
    assert any(line.startswith("Best case:") for line in lines)
    assert len(progress_events) == 40
    assert len(strategy_progress_events) == 48
    assert any("Finished path analysis." in line for line in lines)


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
    assert "matches=" in _footer_prompt(controller)
    assert "pos=ALL" in _footer_prompt(controller)
    assert "? help" in _footer_prompt(controller)


def test_cli_help_overlay_explains_scores(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )

    controller.toggle_help()

    assert controller.help_active is True
    assert "BayesianDraft Help" in controller.view_lines()
    assert any("avg VORP" in line for line in controller.view_lines())
    assert "mode=HELP" in _footer_prompt(controller)

    controller.toggle_help()

    assert controller.help_active is False


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
    assert "matches" in controller.status_message
    assert "mode=SEARCH" in _footer_prompt(controller)
    assert {ranking.position.value for ranking in controller.selectable_rankings()} == {"RB"}

    _handle_live_search_key(controller, 127)

    assert controller.search_query == "r"

    _handle_live_search_key(controller, ord("\n"))

    assert controller.search_active is False


def test_cli_rankings_can_start_search_by_typing(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )
    controller.move_view(1)

    assert _is_quick_search_key(ord("r")) is True
    controller.start_search()
    controller.append_search_character("r")
    controller.append_search_character("b")

    assert controller.search_query == "rb"
    assert controller.selectable_rankings()
    assert {ranking.position.value for ranking in controller.selectable_rankings()} == {"RB"}


def test_cli_live_search_preserves_selected_match(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )
    controller.move_view(1)
    controller.move_selection(1)
    selected_player_id = controller.selectable_rankings()[controller.selection_index].player_id
    selected_name = controller.selectable_rankings()[controller.selection_index].full_name

    controller.start_search()
    for character in selected_name[:8]:
        _handle_live_search_key(controller, ord(character))

    assert (
        controller.selectable_rankings()[controller.selection_index].player_id
        == selected_player_id
    )


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


def test_cli_controller_logs_decision_audit_event(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    audit_path = tmp_path / "audit.json"
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(
            save_path=tmp_path / "draft.json",
            audit_path=audit_path,
        ),
    )

    controller.draft_selected_player()
    audit_log = load_decision_audit(audit_path)

    assert len(audit_log.events) == 1
    assert audit_log.events[0].selected_player_id == "rb_001"
    assert audit_log.events[0].recommended_player_id == "rb_001"
    assert audit_log.events[0].alternative_player_ids
    assert "Audit logged" in controller.status_message


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


def test_cli_controller_supports_page_and_boundary_navigation(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=tmp_path / "draft.json"),
    )
    controller.move_view(1)

    controller.page_selection(1, page_size=4)
    assert controller.selection_index == 4

    controller.jump_selection(to_end=True)
    assert controller.selection_index == len(controller.selectable_rankings()) - 1

    controller.jump_selection(to_end=False)
    assert controller.selection_index == 0

    controller.view_index = 3
    controller.jump_selection(to_end=True)
    assert controller.manager_selection_index == 13

    controller.jump_selection(to_end=False)
    assert controller.manager_selection_index == 0


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


def test_cli_controller_loads_existing_save(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    save_path = tmp_path / "draft.json"
    saved_state = state.record_pick("rb_001")
    saved_state.save(save_path)

    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(save_path=save_path, load_existing_save=True),
    )

    assert controller.state.current_overall_pick == 2
    assert controller.state.completed_picks[0].player_id == "rb_001"
    assert "Loaded saved draft" in controller.status_message


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
    assert any("Path analysis:" in line for line in recommendation_lines)
    assert any("Best overall recommendation" in line for line in recommendation_lines)
    assert any("RB need=" in line for line in recommendation_lines)
    assert any("WR need=" in line for line in recommendation_lines)
    assert any("Breakdown:" in line for line in recommendation_lines)
    assert any("phase=" in line for line in recommendation_lines)
    assert any("drop" in line and "risk" in line for line in recommendation_lines)
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


def test_cli_recommendations_use_cached_path_guidance_on_user_pick(tmp_path: Path) -> None:
    snapshot, state = load_snapshot_and_draft_state()
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(
            save_path=tmp_path / "draft.json",
            scenario_path=Path("data/fixtures/rehearsal_user_pick_8.json"),
        ),
    )
    controller.view_index = 2

    assert any("Path analysis: run Simulation with a" in line for line in controller.view_lines())

    controller.run_path_analysis()
    lines = controller.view_lines()

    assert any("Path analysis: best next-pick direction" in line for line in lines)

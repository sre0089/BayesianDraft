import curses
from dataclasses import dataclass
from pathlib import Path

from bayesiandraft.data import PlayerSnapshot, build_snapshot_health_report
from bayesiandraft.draft import (
    DraftState,
    DraftStateError,
    apply_rehearsal_scenario,
    build_roster_balance_report,
    load_rehearsal_scenario,
    summarize_draft_state,
)
from bayesiandraft.rankings import RankingRow, build_baseline_rankings
from bayesiandraft.recommendations import RecommendationResult, recommend_players
from bayesiandraft.simulation import benchmark_remaining_draft

VIEWS = ("Summary", "Rankings", "Recommendations", "Roster", "Health", "Simulation", "Picks")


@dataclass(frozen=True)
class CliDraftConfig:
    save_path: Path
    scenario_path: Path | None = None


class CliDraftController:
    def __init__(
        self,
        *,
        snapshot: PlayerSnapshot,
        state: DraftState,
        config: CliDraftConfig,
    ) -> None:
        self.snapshot = snapshot
        self.state = state
        self.config = config
        self.view_index = 0
        self.selection_index = 0
        self.search_query = ""
        self.status_message = "Ready."
        self._rankings = build_baseline_rankings(snapshot)

        if config.scenario_path is not None:
            self.state = apply_rehearsal_scenario(
                self.state,
                load_rehearsal_scenario(config.scenario_path),
            )
            self.status_message = f"Loaded scenario: {config.scenario_path}"

    @property
    def current_view(self) -> str:
        return VIEWS[self.view_index]

    def move_view(self, delta: int) -> None:
        self.view_index = (self.view_index + delta) % len(VIEWS)
        self.selection_index = 0

    def move_selection(self, delta: int) -> None:
        item_count = max(len(self.selectable_rankings()), 1)
        self.selection_index = max(0, min(self.selection_index + delta, item_count - 1))

    def set_search(self, query: str) -> None:
        self.search_query = query.strip()
        self.selection_index = 0
        self.status_message = (
            "Search cleared." if not self.search_query else f"Search: {self.search_query}"
        )

    def selectable_rankings(self) -> list[RankingRow]:
        available_ids = set(self.state.available_player_ids)
        rows = [ranking for ranking in self._rankings if ranking.player_id in available_ids]
        if not self.search_query:
            return rows

        query = self.search_query.lower()
        return [
            ranking
            for ranking in rows
            if query in ranking.full_name.lower()
            or query in ranking.position.value.lower()
            or query in ranking.player_id.lower()
        ]

    def recommendation(self) -> RecommendationResult | None:
        try:
            return recommend_players(self.state, self._rankings)
        except ValueError:
            return None

    def draft_selected_player(self) -> None:
        rows = self.selectable_rankings()
        if not rows:
            self.status_message = "No available player selected."
            return

        player = rows[self.selection_index]
        try:
            self.state = self.state.record_pick(player.player_id)
        except DraftStateError as exc:
            self.status_message = str(exc)
            return

        max_index = max(len(self.selectable_rankings()) - 1, 0)
        self.selection_index = min(self.selection_index, max_index)
        self.status_message = (
            f"Drafted {player.full_name} for {self.state.completed_picks[-1].manager_id}."
        )

    def undo(self) -> None:
        try:
            self.state = self.state.undo()
            self.status_message = "Undid last pick."
        except DraftStateError as exc:
            self.status_message = str(exc)

    def redo(self) -> None:
        try:
            self.state = self.state.redo()
            self.status_message = "Redid pick."
        except DraftStateError as exc:
            self.status_message = str(exc)

    def save(self) -> None:
        self.config.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.state.save(self.config.save_path)
        self.status_message = f"Saved draft to {self.config.save_path}"

    def view_lines(self) -> list[str]:
        view = self.current_view
        if view == "Summary":
            return self._summary_lines()
        if view == "Rankings":
            return self._ranking_lines()
        if view == "Recommendations":
            return self._recommendation_lines()
        if view == "Roster":
            return self._roster_lines()
        if view == "Health":
            return self._health_lines()
        if view == "Simulation":
            return self._simulation_lines()
        return self._pick_lines()

    def _summary_lines(self) -> list[str]:
        summary = summarize_draft_state(self.state)
        next_pick = "-" if summary.next_user_pick is None else str(summary.next_user_pick)
        return [
            f"Draft ID: {summary.draft_id}",
            f"Current pick: {summary.current_overall_pick}",
            f"On clock: {summary.manager_on_clock}",
            f"Completed picks: {summary.completed_pick_count}",
            f"Available players: {summary.available_player_count}",
            f"Your roster size: {summary.user_roster_size}",
            f"Your next pick: {next_pick}",
            "",
            "Shortcuts: left/right views, up/down select, enter/d draft, / search.",
            "More: c clear, u undo, r redo, s save, q quit.",
        ]

    def _ranking_lines(self) -> list[str]:
        rows = self.selectable_rankings()
        if not rows:
            return ["No available players match the current filter."]
        return [
            _ranking_line(row, selected=index == self.selection_index)
            for index, row in enumerate(rows[:40])
        ]

    def _recommendation_lines(self) -> list[str]:
        recommendation = self.recommendation()
        if recommendation is None:
            return ["No recommendations are available."]
        rows = [recommendation.primary, *recommendation.alternatives]
        lines = ["Primary recommendation and alternatives:", ""]
        for row in rows:
            ranking = self._ranking_by_id(row.player_id)
            name = ranking.full_name if ranking else row.player_id
            lines.append(
                f"{row.rank:>3}. {name:<28} score={row.total_score:>7.1f} "
                f"conf={row.confidence:.0%} avail={row.next_pick_availability:.0%}"
            )
            lines.extend(f"     - {item}" for item in row.explanation)
            lines.append("")
        return lines

    def _roster_lines(self) -> list[str]:
        user_manager_id = self.state.league_config.league.user_manager_id
        report = build_roster_balance_report(self.state, user_manager_id)
        roster = self.state.rosters[user_manager_id]
        lines = [f"Roster balance for {user_manager_id}", ""]
        for position in report.positions:
            lines.append(
                f"{position.position:<3} current={position.current_count:<2} "
                f"need={position.remaining_starter_need:<2} surplus={position.surplus:<2}"
            )
        lines.append("")
        if not roster.player_ids:
            lines.append("No players drafted yet.")
        else:
            for player_id in roster.player_ids:
                player = self.state.players[player_id]
                lines.append(f"{player.position:<3} {player.full_name}")
        return lines

    def _health_lines(self) -> list[str]:
        health = build_snapshot_health_report(self.snapshot)
        lines = [
            f"Snapshot: {health.snapshot_id}",
            f"Players: {health.player_count}",
            f"Projections: {health.projection_count} ({health.projection_coverage:.0%})",
            f"ADP: {health.adp_count} ({health.adp_coverage:.0%})",
            f"Injuries: {health.injury_count}",
            "",
        ]
        if health.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in health.warnings)
        else:
            lines.append("No snapshot warnings.")
        return lines

    def _simulation_lines(self) -> list[str]:
        result = benchmark_remaining_draft(self.state, self._rankings)
        return [
            "Seeded simulation smoke benchmark",
            "",
            f"Completed picks after simulation: {result.completed_pick_count}",
            f"Seed: {result.seed}",
            f"Runtime seconds: {result.elapsed_seconds}",
            f"Stopped reason: {result.stopped_reason}",
        ]

    def _pick_lines(self) -> list[str]:
        if not self.state.completed_picks:
            return ["No picks recorded yet."]
        lines = []
        for pick in self.state.completed_picks[-40:]:
            player = self.state.players[pick.player_id]
            lines.append(
                f"{pick.overall_pick:>3}. R{pick.round}.{pick.round_pick:<2} "
                f"{pick.manager_id:<14} {player.position:<3} {player.full_name}"
            )
        return lines

    def _ranking_by_id(self, player_id: str) -> RankingRow | None:
        for ranking in self._rankings:
            if ranking.player_id == player_id:
                return ranking
        return None


def run_tui(controller: CliDraftController) -> None:
    curses.wrapper(_curses_main, controller)


def _curses_main(screen: curses.window, controller: CliDraftController) -> None:
    curses.curs_set(0)
    screen.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)

    while True:
        _draw(screen, controller)
        key = screen.getch()
        if key in {ord("q"), 27}:
            return
        if key in {curses.KEY_RIGHT, ord("\t")}:
            controller.move_view(1)
        elif key == curses.KEY_LEFT:
            controller.move_view(-1)
        elif key == curses.KEY_DOWN:
            controller.move_selection(1)
        elif key == curses.KEY_UP:
            controller.move_selection(-1)
        elif key in {ord("\n"), ord("\r"), ord("d")}:
            controller.draft_selected_player()
        elif key == ord("u"):
            controller.undo()
        elif key == ord("r"):
            controller.redo()
        elif key == ord("s"):
            controller.save()
        elif key == ord("c"):
            controller.set_search("")
        elif key == ord("/"):
            controller.set_search(_prompt(screen, "Search players: "))


def _draw(screen: curses.window, controller: CliDraftController) -> None:
    screen.erase()
    height, width = screen.getmaxyx()
    _draw_header(screen, controller, width)
    _draw_tabs(screen, controller, width)
    _draw_body(screen, controller, height, width)
    _draw_footer(screen, controller, height, width)
    screen.refresh()


def _draw_header(screen: curses.window, controller: CliDraftController, width: int) -> None:
    title = " BayesianDraft CLI "
    summary = summarize_draft_state(controller.state)
    status = (
        f"Pick {summary.current_overall_pick} | On clock {summary.manager_on_clock} | "
        f"Available {summary.available_player_count}"
    )
    screen.addnstr(0, 0, title.ljust(width), width, curses.color_pair(1) | curses.A_BOLD)
    screen.addnstr(1, 0, status.ljust(width), width)


def _draw_tabs(screen: curses.window, controller: CliDraftController, width: int) -> None:
    x = 0
    for index, view in enumerate(VIEWS):
        label = f" {view} "
        attrs = curses.color_pair(2) | curses.A_BOLD if index == controller.view_index else 0
        if x + len(label) < width:
            screen.addstr(3, x, label, attrs)
        x += len(label) + 1


def _draw_body(
    screen: curses.window,
    controller: CliDraftController,
    height: int,
    width: int,
) -> None:
    top = 5
    max_lines = max(height - 8, 1)
    for offset, line in enumerate(controller.view_lines()[:max_lines]):
        attrs = curses.A_REVERSE if line.startswith(">") else 0
        screen.addnstr(top + offset, 0, line[: width - 1], width - 1, attrs)


def _draw_footer(
    screen: curses.window,
    controller: CliDraftController,
    height: int,
    width: int,
) -> None:
    search = f"Filter: {controller.search_query or '-'}"
    screen.addnstr(height - 2, 0, search.ljust(width), width, curses.color_pair(3))
    screen.addnstr(height - 1, 0, controller.status_message.ljust(width), width)


def _prompt(screen: curses.window, prompt: str) -> str:
    height, width = screen.getmaxyx()
    curses.echo()
    curses.curs_set(1)
    screen.addnstr(height - 1, 0, " " * width, width)
    screen.addnstr(height - 1, 0, prompt, width - 1)
    screen.refresh()
    value = screen.getstr(height - 1, len(prompt), max(width - len(prompt) - 1, 1))
    curses.noecho()
    curses.curs_set(0)
    return value.decode("utf-8").strip()


def _ranking_line(row: RankingRow, *, selected: bool) -> str:
    marker = ">" if selected else " "
    return (
        f"{marker} {row.overall_rank:>3}. {row.full_name:<28} {row.position.value:<3} "
        f"tier={row.tier:<2} proj={row.projected_points:>6.1f} "
        f"vorp={row.vorp:>6.1f} adp={row.adp or 0:>6.1f}"
    )

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

VIEWS = (
    "Summary",
    "Rankings",
    "Recommendations",
    "Managers",
    "Roster",
    "Health",
    "Simulation",
    "Picks",
)
POSITIONS = ("QB", "RB", "WR", "TE", "DST", "K")


@dataclass(frozen=True)
class CliDraftConfig:
    save_path: Path
    scenario_path: Path | None = None
    auto_pick_to_user: bool = False


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
        self.manager_selection_index = self._default_manager_selection_index()
        self.search_query = ""
        self.status_message = "Ready."
        self._rankings = build_baseline_rankings(snapshot)
        self._players_by_id = {player.player_id: player for player in snapshot.players}
        self._projections_by_player_id = {
            projection.player_id: projection for projection in snapshot.projections
        }
        self._adp_by_player_id = {adp.player_id: adp for adp in snapshot.adp}

        if config.scenario_path is not None:
            self.state = apply_rehearsal_scenario(
                self.state,
                load_rehearsal_scenario(config.scenario_path),
            )
            self.status_message = f"Loaded scenario: {config.scenario_path}"
        elif config.auto_pick_to_user:
            auto_pick_count = self.auto_pick_to_user()
            self.status_message = f"Auto-drafted {auto_pick_count} picks to user pick."

    @property
    def current_view(self) -> str:
        return VIEWS[self.view_index]

    def move_view(self, delta: int) -> None:
        self.view_index = (self.view_index + delta) % len(VIEWS)
        self.selection_index = 0

    def move_selection(self, delta: int) -> None:
        if self.current_view == "Managers":
            manager_count = len(self.state.league_config.draft_order)
            self.manager_selection_index = max(
                0,
                min(self.manager_selection_index + delta, manager_count - 1),
            )
            return

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

    def auto_pick_to_user(self) -> int:
        user_manager_id = self.state.league_config.league.user_manager_id
        count = 0
        while self.state.manager_on_clock != user_manager_id and not self.state.is_complete:
            rows = self.selectable_rankings()
            if not rows:
                break
            self.state = self.state.record_pick(rows[0].player_id)
            count += 1
        self.selection_index = 0
        return count

    def view_lines(self) -> list[str]:
        view = self.current_view
        if view == "Summary":
            return self._summary_lines()
        if view == "Rankings":
            return self._ranking_lines()
        if view == "Recommendations":
            return self._recommendation_lines()
        if view == "Managers":
            return self._manager_lines()
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
            r"  ____                          _             ____             __ _   ",
            r" | __ )  __ _ _   _  ___  ___ (_) __ _ _ __ |  _ \ _ __ __ _ / _| |_ ",
            r" |  _ \ / _` | | | |/ _ \/ __|| |/ _` | '_ \| | | | '__/ _` | |_| __|",
            r" | |_) | (_| | |_| |  __/\__ \| | (_| | | | | |_| | | | (_| |  _| |_ ",
            r" |____/ \__,_|\__, |\___||___// |\__,_|_| |_|____/|_|  \__,_|_|  \__|",
            r"              |___/         |__/                                      ",
            "",
            f"Draft ID: {summary.draft_id}",
            f"Current pick: {summary.current_overall_pick}",
            f"On clock: {summary.manager_on_clock}",
            f"Completed picks: {summary.completed_pick_count}",
            f"Available players: {summary.available_player_count}",
            f"Your roster size: {summary.user_roster_size}",
            f"Your next pick: {next_pick}",
            "",
            "Live entry: draft the selected player for whoever is currently on clock.",
            (
                "Shortcuts: left/right views, up/down select players/managers, "
                "enter/d draft, / search."
            ),
            "More: c clear, u undo, r redo, s save, q quit.",
        ]

    def _ranking_lines(self) -> list[str]:
        rows = self.selectable_rankings()
        if not rows:
            return ["No available players match the current filter."]
        lines = [
            _ranking_line(row, selected=index == self.selection_index)
            for index, row in enumerate(rows[:30])
        ]
        selected = rows[self.selection_index]
        lines.extend(["", *self._selected_player_detail_lines(selected)])
        return lines

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

    def _manager_lines(self) -> list[str]:
        selected_manager_id = self._selected_manager_id()
        selected_roster = self.state.rosters[selected_manager_id]
        lines = [
            "Managers",
            "Use up/down to inspect every roster as picks come in.",
            "",
        ]
        for index, manager in enumerate(self.state.league_config.draft_order):
            roster = self.state.rosters[manager.id]
            marker = ">" if index == self.manager_selection_index else " "
            on_clock = "*" if manager.id == self.state.manager_on_clock else " "
            user = "YOU" if manager.id == self.state.league_config.league.user_manager_id else "   "
            lines.append(
                f"{marker}{on_clock} {self._manager_label(manager.id):<12} "
                f"{user} picks={len(roster.player_ids):<2} "
                f"{self._position_count_text(roster.positional_counts)}"
            )
        lines.extend(["", f"Roster: {self._manager_label(selected_manager_id)}"])
        if not selected_roster.player_ids:
            lines.append("No picks yet.")
        else:
            for player_id in selected_roster.player_ids:
                player = self.state.players[player_id]
                lines.append(
                    f"{self._team_badge(player.nfl_team_id)} {player.position:<3} "
                    f"{player.full_name}"
                )
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

    def _default_manager_selection_index(self) -> int:
        user_manager_id = self.state.league_config.league.user_manager_id
        for index, manager in enumerate(self.state.league_config.draft_order):
            if manager.id == user_manager_id:
                return index
        return 0

    def _selected_manager_id(self) -> str:
        return self.state.league_config.draft_order[self.manager_selection_index].id

    def _manager_label(self, manager_id: str) -> str:
        if manager_id == self.state.league_config.league.user_manager_id:
            return "Your Team"
        return manager_id.replace("manager_", "Team ")

    def _position_count_text(self, counts: dict[str, int]) -> str:
        return " ".join(f"{position}:{counts.get(position, 0)}" for position in POSITIONS)

    def _team_badge(self, team: str | None) -> str:
        return f"[{team or 'FA':^3}]"

    def _selected_player_detail_lines(self, ranking: RankingRow) -> list[str]:
        player = self._players_by_id.get(ranking.player_id)
        projection = self._projections_by_player_id.get(ranking.player_id)
        adp = self._adp_by_player_id.get(ranking.player_id)
        team = player.nfl_team_id if player and player.nfl_team_id else "-"
        bye = str(player.bye_week) if player and player.bye_week is not None else "-"
        games = (
            "-"
            if projection is None or projection.games_played_mean is None
            else f"{projection.games_played_mean:.1f}"
        )
        adp_text = "-" if adp is None else f"{adp.overall_adp:.1f}"
        position_adp = "-" if adp is None or adp.position_adp is None else f"{adp.position_adp:.1f}"
        market_rank = "-" if adp is None or adp.rank is None else str(adp.rank)
        adp_delta = "-" if ranking.adp_delta is None else f"{ranking.adp_delta:+.1f}"
        return [
            f"Selected: {ranking.full_name} ({ranking.position.value}) team={team} bye={bye}",
            (
                f"Projection: mean={ranking.projected_points:.1f} "
                f"median={ranking.median:.1f} floor={ranking.floor:.1f} "
                f"ceiling={ranking.ceiling:.1f} games={games}"
            ),
            (
                f"Value: vorp={ranking.vorp:.1f} starter={ranking.value_above_starter:.1f} "
                f"tier={ranking.tier} pos_rank={ranking.position_rank}"
            ),
            (
                f"Market: adp={adp_text} pos_adp={position_adp} rank={market_rank} "
                f"delta={adp_delta} sleeper={ranking.sleeper_score:.2f} "
                f"fade={ranking.fade_score:.2f}"
            ),
        ]


def run_tui(controller: CliDraftController) -> None:
    curses.wrapper(_curses_main, controller)


def _curses_main(screen: curses.window, controller: CliDraftController) -> None:
    _set_cursor_visibility(0)
    screen.keypad(True)
    _init_colors()

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
    if height < 10 or width < 44:
        _safe_addnstr(screen, 0, 0, "Terminal is too small for BayesianDraft CLI.", width)
        screen.refresh()
        return
    _draw_header(screen, controller, width)
    _draw_tabs(screen, controller, width)
    _draw_body(screen, controller, height, width)
    _draw_footer(screen, controller, height, width)
    screen.refresh()


def _draw_header(screen: curses.window, controller: CliDraftController, width: int) -> None:
    summary = summarize_draft_state(controller.state)
    brand = " BD // BayesianDraft "
    status = (
        f"Pick {summary.current_overall_pick}/{controller.state.total_picks}  "
        f"Round {controller.state.current_round or '-'}  Clock {summary.manager_on_clock}  "
        f"Next user {summary.next_user_pick or '-'}"
    )
    _safe_addnstr(screen, 0, 0, brand.ljust(width), width, curses.color_pair(1) | curses.A_BOLD)
    _safe_addnstr(screen, 1, 0, status.ljust(width), width, curses.A_BOLD)
    progress = _progress_bar(summary.completed_pick_count, controller.state.total_picks, width - 24)
    _safe_addnstr(
        screen,
        2,
        0,
        f" Draft progress {progress} {summary.available_player_count} available".ljust(width),
        width,
        curses.color_pair(3),
    )


def _draw_tabs(screen: curses.window, controller: CliDraftController, width: int) -> None:
    x = 0
    for index, view in enumerate(VIEWS):
        label = f" {view} "
        attrs = curses.color_pair(2) | curses.A_BOLD if index == controller.view_index else 0
        if x + len(label) < width:
            _safe_addnstr(screen, 4, x, label, width - x, attrs)
        x += len(label) + 1


def _draw_body(
    screen: curses.window,
    controller: CliDraftController,
    height: int,
    width: int,
) -> None:
    top = 6
    body_height = max(height - 9, 1)
    if controller.current_view == "Rankings" and width >= 104:
        _draw_rankings_workspace(screen, controller, top, 0, body_height, width)
        return
    if controller.current_view == "Managers" and width >= 96:
        _draw_manager_workspace(screen, controller, top, 0, body_height, width)
        return

    _draw_box(screen, top, 0, body_height, width, controller.current_view)
    _draw_lines(
        screen,
        controller.view_lines(),
        top + 1,
        2,
        max(body_height - 2, 0),
        max(width - 4, 1),
    )


def _draw_footer(
    screen: curses.window,
    controller: CliDraftController,
    height: int,
    width: int,
) -> None:
    search = f"Filter: {controller.search_query or '-'}"
    _safe_addnstr(screen, height - 2, 0, search.ljust(width), width, curses.color_pair(3))
    _safe_addnstr(screen, height - 1, 0, controller.status_message.ljust(width), width)


def _progress_bar(completed: int, total: int, width: int) -> str:
    bar_width = max(min(width, 40), 8)
    filled = 0 if total == 0 else round((completed / total) * bar_width)
    return "[" + "#" * filled + "." * (bar_width - filled) + "]"


def _draw_box(
    screen: curses.window,
    y: int,
    x: int,
    height: int,
    width: int,
    title: str,
) -> None:
    if height < 3 or width < 8:
        return

    horizontal = "-" * max(width - 2, 0)
    _safe_addnstr(screen, y, x, "+" + horizontal + "+", width)
    for row in range(y + 1, y + height - 1):
        _safe_addnstr(screen, row, x, "|", 1)
        _safe_addnstr(screen, row, x + width - 1, "|", 1)
    _safe_addnstr(screen, y + height - 1, x, "+" + horizontal + "+", width)

    label = f" {title} "
    if len(label) < width - 2:
        _safe_addnstr(screen, y, x + 2, label, width - 4, curses.color_pair(1) | curses.A_BOLD)


def _draw_lines(
    screen: curses.window,
    lines: list[str],
    y: int,
    x: int,
    max_lines: int,
    width: int,
) -> None:
    for offset, line in enumerate(lines[:max_lines]):
        attrs = curses.A_REVERSE if line.startswith(">") else 0
        _safe_addnstr(screen, y + offset, x, line, width, attrs)


def _draw_rankings_workspace(
    screen: curses.window,
    controller: CliDraftController,
    y: int,
    x: int,
    height: int,
    width: int,
) -> None:
    left_width = min(max(70, int(width * 0.64)), width - 34)
    right_width = width - left_width - 1
    rows = controller.selectable_rankings()
    selected = rows[controller.selection_index] if rows else None

    _draw_box(screen, y, x, height, left_width, "Available Players")
    ranking_lines = [
        _ranking_line(row, selected=index == controller.selection_index)
        for index, row in enumerate(rows[: max(height - 2, 0)])
    ]
    if not ranking_lines:
        ranking_lines = ["No available players match the current filter."]
    _draw_lines(screen, ranking_lines, y + 1, x + 2, height - 2, left_width - 4)

    _draw_box(screen, y, x + left_width + 1, height, right_width, "Player Detail")
    detail_lines = (
        ["No player selected."]
        if selected is None
        else [
            f"{controller._team_badge(selected.nfl_team_id)} {selected.full_name}",
            "",
            *controller._selected_player_detail_lines(selected),
            "",
            "Enter/d records this player for the manager on clock.",
        ]
    )
    _draw_lines(screen, detail_lines, y + 1, x + left_width + 3, height - 2, right_width - 4)


def _draw_manager_workspace(
    screen: curses.window,
    controller: CliDraftController,
    y: int,
    x: int,
    height: int,
    width: int,
) -> None:
    left_width = min(58, width // 2)
    right_width = width - left_width - 1
    selected_manager_id = controller._selected_manager_id()
    selected_roster = controller.state.rosters[selected_manager_id]

    _draw_box(screen, y, x, height, left_width, "Managers")
    manager_lines = []
    for index, manager in enumerate(controller.state.league_config.draft_order):
        roster = controller.state.rosters[manager.id]
        marker = ">" if index == controller.manager_selection_index else " "
        clock = "*" if manager.id == controller.state.manager_on_clock else " "
        user = (
            "YOU"
            if manager.id == controller.state.league_config.league.user_manager_id
            else "   "
        )
        manager_lines.append(
            f"{marker}{clock} {controller._manager_label(manager.id):<12} "
            f"{user} {len(roster.player_ids):>2} picks"
        )
    _draw_lines(screen, manager_lines, y + 1, x + 2, height - 2, left_width - 4)

    _draw_box(
        screen,
        y,
        x + left_width + 1,
        height,
        right_width,
        f"Roster: {controller._manager_label(selected_manager_id)}",
    )
    roster_lines = [
        controller._position_count_text(selected_roster.positional_counts),
        "",
    ]
    if not selected_roster.player_ids:
        roster_lines.append("No picks yet.")
    else:
        for player_id in selected_roster.player_ids:
            player = controller.state.players[player_id]
            roster_lines.append(
                f"{controller._team_badge(player.nfl_team_id)} {player.position:<3} "
                f"{player.full_name}"
            )
    _draw_lines(screen, roster_lines, y + 1, x + left_width + 3, height - 2, right_width - 4)


def _prompt(screen: curses.window, prompt: str) -> str:
    height, width = screen.getmaxyx()
    curses.echo()
    _set_cursor_visibility(1)
    _safe_addnstr(screen, height - 1, 0, " " * width, width)
    _safe_addnstr(screen, height - 1, 0, prompt, width)
    screen.refresh()
    value = screen.getstr(height - 1, len(prompt), max(width - len(prompt) - 1, 1))
    curses.noecho()
    _set_cursor_visibility(0)
    return value.decode("utf-8").strip()


def _init_colors() -> None:
    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
    except curses.error:
        return


def _set_cursor_visibility(visibility: int) -> None:
    try:
        curses.curs_set(visibility)
    except curses.error:
        return


def _safe_addnstr(
    screen: curses.window,
    y: int,
    x: int,
    text: str,
    width: int,
    attrs: int = 0,
) -> None:
    height, screen_width = screen.getmaxyx()
    if y < 0 or y >= height or x < 0 or x >= screen_width:
        return

    max_width = max(min(width, screen_width - x), 0)
    if max_width == 0:
        return

    try:
        screen.addnstr(y, x, text, max_width, attrs)
    except curses.error:
        return


def _ranking_line(row: RankingRow, *, selected: bool) -> str:
    marker = ">" if selected else " "
    return (
        f"{marker} {row.overall_rank:>3}. {row.full_name:<28} {row.position.value:<3} "
        f"tier={row.tier:<2} proj={row.projected_points:>6.1f} "
        f"vorp={row.vorp:>6.1f} adp={row.adp or 0:>6.1f}"
    )

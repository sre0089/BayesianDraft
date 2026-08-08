import curses
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from bayesiandraft import __version__
from bayesiandraft.audit import DecisionAuditEvent, append_decision_event
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
from bayesiandraft.recommendations import (
    CandidateOptimizationResult,
    CandidateOptimizerConfig,
    PositionalRecommendationGroup,
    RecommendationResult,
    RecommendationScore,
    optimize_candidates,
    recommend_players,
    recommend_players_by_needed_position,
)
from bayesiandraft.simulation import (
    DraftSimulationConfig,
    LeaguePathAnalysisResult,
    LeaguePathProgress,
    LeaguePathProgressCallback,
    LeaguePathSimulationConfig,
    StrategyPathAnalysisResult,
    StrategyPathProgress,
    StrategyPathProgressCallback,
    StrategyPathSimulationConfig,
    analyze_league_paths,
    analyze_user_strategy_paths,
)

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
COMPACT_LOGO_LINES = (
    r"  ____  ____  ",
    r" | __ )|  _ \ ",
    r" |  _ \| | | |",
    r" | |_) | |_| |",
    r" |____/|____/ ",
)


@dataclass(frozen=True)
class CliDraftConfig:
    save_path: Path
    audit_path: Path | None = None
    scenario_path: Path | None = None
    auto_pick_to_user: bool = False
    autosave: bool = True
    load_existing_save: bool = False


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
        self.ranking_scroll_offset = 0
        self.manager_selection_index = self._default_manager_selection_index()
        self.search_query = ""
        self.position_filter = "ALL"
        self.search_active = False
        self.status_message = "Ready."
        self.last_save_message = "Not saved yet."
        self._rankings = build_baseline_rankings(snapshot)
        self._players_by_id = {player.player_id: player for player in snapshot.players}
        self._projections_by_player_id = {
            projection.player_id: projection for projection in snapshot.projections
        }
        self._adp_by_player_id = {adp.player_id: adp for adp in snapshot.adp}
        self._path_analysis_cache_key: tuple[str, ...] | None = None
        self._path_analysis_cache: tuple[
            LeaguePathAnalysisResult,
            StrategyPathAnalysisResult,
        ] | None = None
        self.path_analysis_logs: list[str] = [
            "Press a on this tab to run multi-path draft analysis."
        ]

        if config.load_existing_save and config.save_path.exists():
            self.state = DraftState.load(config.save_path)
            self.status_message = f"Loaded saved draft from {config.save_path}"
            self.last_save_message = f"Loaded save {config.save_path}"
        elif config.scenario_path is not None:
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
        self.ranking_scroll_offset = 0

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
        self._sync_ranking_scroll(visible_count=30)

    def page_selection(self, delta: int, *, page_size: int = 10) -> None:
        self.move_selection(delta * page_size)

    def jump_selection(self, *, to_end: bool) -> None:
        if self.current_view == "Managers":
            self.manager_selection_index = (
                len(self.state.league_config.draft_order) - 1 if to_end else 0
            )
            return

        item_count = len(self.selectable_rankings())
        self.selection_index = max(item_count - 1, 0) if to_end else 0
        self._sync_ranking_scroll(visible_count=30)

    def set_search(self, query: str) -> None:
        selected_player_id = self._selected_ranking_player_id()
        self.search_query = query.strip()
        self._restore_selection(selected_player_id)
        self.status_message = self._search_status_message()

    def start_search(self) -> None:
        self.search_active = True
        self.status_message = "Live search: type to filter, Enter/Esc to finish."

    def finish_search(self) -> None:
        self.search_active = False
        self.status_message = self._search_status_message()

    def append_search_character(self, character: str) -> None:
        if not character.isprintable():
            return
        selected_player_id = self._selected_ranking_player_id()
        self.search_query += character
        self._restore_selection(selected_player_id)
        self.status_message = self._search_status_message()

    def backspace_search(self) -> None:
        selected_player_id = self._selected_ranking_player_id()
        self.search_query = self.search_query[:-1]
        self._restore_selection(selected_player_id)
        self.status_message = self._search_status_message()

    def cycle_position_filter(self, delta: int) -> None:
        options = ("ALL", *POSITIONS)
        current_index = options.index(self.position_filter)
        self.position_filter = options[(current_index + delta) % len(options)]
        self.selection_index = 0
        self.ranking_scroll_offset = 0
        self.status_message = f"Position filter: {self.position_filter}"

    def set_position_filter(self, position: str) -> None:
        normalized = position.upper()
        if normalized not in ("ALL", *POSITIONS):
            return
        self.position_filter = normalized
        self.selection_index = 0
        self.ranking_scroll_offset = 0
        self.status_message = f"Position filter: {self.position_filter}"

    def selectable_rankings(self) -> list[RankingRow]:
        available_ids = set(self.state.available_player_ids)
        rows = [ranking for ranking in self._rankings if ranking.player_id in available_ids]
        if self.position_filter != "ALL":
            rows = [ranking for ranking in rows if ranking.position.value == self.position_filter]
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

    def positional_recommendations(self) -> list[PositionalRecommendationGroup]:
        return recommend_players_by_needed_position(self.state, self._rankings)

    def rollout_recommendation(self) -> CandidateOptimizationResult | None:
        try:
            return optimize_candidates(
                self.state,
                self._rankings,
                config=CandidateOptimizerConfig(limit=3, candidate_pool_size=8, simulation_count=8),
            )
        except ValueError:
            return None

    def draft_selected_player(self) -> None:
        rows = self.selectable_rankings()
        if not rows:
            self.status_message = "No available player selected."
            return

        player = rows[self.selection_index]
        try:
            recommendation = self.recommendation()
            self.state = self.state.record_pick(player.player_id)
        except DraftStateError as exc:
            self.status_message = str(exc)
            return

        self._invalidate_path_analysis()
        max_index = max(len(self.selectable_rankings()) - 1, 0)
        self.selection_index = min(self.selection_index, max_index)
        self._sync_ranking_scroll(visible_count=30)
        autosave_message = self._autosave()
        audit_message = self._audit_pick(player.player_id, recommendation)
        self.status_message = (
            f"Drafted {player.full_name} for {self.state.completed_picks[-1].manager_id}."
            f" {autosave_message} {audit_message}"
        )

    def undo(self) -> None:
        try:
            self.state = self.state.undo()
            self._invalidate_path_analysis()
            autosave_message = self._autosave()
            self.status_message = f"Undid last pick. {autosave_message}"
        except DraftStateError as exc:
            self.status_message = str(exc)

    def redo(self) -> None:
        try:
            self.state = self.state.redo()
            self._invalidate_path_analysis()
            autosave_message = self._autosave()
            self.status_message = f"Redid pick. {autosave_message}"
        except DraftStateError as exc:
            self.status_message = str(exc)

    def save(self) -> None:
        self._save_state()
        self.status_message = f"Saved draft to {self.config.save_path}"

    def _autosave(self) -> str:
        if not self.config.autosave:
            return "Autosave off."
        self._save_state()
        return self.last_save_message

    def _save_state(self) -> None:
        self.config.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.state.save(self.config.save_path)
        saved_at = datetime.now().strftime("%H:%M:%S")
        self.last_save_message = f"Autosaved {saved_at} to {self.config.save_path}"

    def _audit_pick(
        self,
        selected_player_id: str,
        recommendation: RecommendationResult | None,
    ) -> str:
        if self.config.audit_path is None:
            return ""
        completed_pick = self.state.completed_picks[-1]
        event = DecisionAuditEvent(
            event_id=f"{self.state.draft_id}-{completed_pick.overall_pick}",
            draft_id=self.state.draft_id,
            overall_pick=completed_pick.overall_pick,
            selected_player_id=selected_player_id,
            recommended_player_id=(
                None if recommendation is None else recommendation.primary.player_id
            ),
            alternative_player_ids=[]
            if recommendation is None
            else [alternative.player_id for alternative in recommendation.alternatives],
            model_versions={"bayesiandraft": __version__},
            data_snapshot_id=self.snapshot.snapshot.snapshot_id,
            notes=[
                (
                    "Accepted primary recommendation."
                    if recommendation is not None
                    and selected_player_id == recommendation.primary.player_id
                    else "Recorded manual draft pick."
                )
            ],
        )
        append_decision_event(self.config.audit_path, event)
        return f"Audit logged to {self.config.audit_path}"

    def auto_pick_to_user(self) -> int:
        user_manager_id = self.state.league_config.league.user_manager_id
        count = 0
        while self.state.manager_on_clock != user_manager_id and not self.state.is_complete:
            rows = self.selectable_rankings()
            if not rows:
                break
            self.state = self.state.record_pick(rows[0].player_id)
            self._invalidate_path_analysis()
            count += 1
        self.selection_index = 0
        if count > 0:
            self._autosave()
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
            "BayesianDraft",
            *COMPACT_LOGO_LINES,
            "",
            f"Version {__version__} - Snapshot {self.snapshot.snapshot.snapshot_id}",
            (
                "Live draft dashboard for projections, scarcity, roster need, "
                "market cost, and next-pick availability."
            ),
            "",
            "CURRENT PICK",
            f">>> {summary.current_overall_pick}/{self.state.total_picks} <<<",
            f"On clock {summary.manager_on_clock}",
            f"Available {summary.available_player_count}",
            f"Your roster {summary.user_roster_size}",
            f"Next user pick {next_pick}",
            self.last_save_message,
            "",
            *self._best_overall_recommendation_lines(include_header=True),
            "",
            "Live entry: draft the selected player for whoever is currently on clock.",
            (
                "Shortcuts: left/right views, up/down select players/managers, "
                "enter/d draft, / search."
            ),
            "More: [/] cycle positions, 0 all, 1-6 positions, c clear, u undo, r redo, s save.",
        ]

    def _ranking_lines(self) -> list[str]:
        rows = self.selectable_rankings()
        if not rows:
            return ["No available players match the current filter."]
        visible_rows = self._visible_rankings(visible_count=30)
        lines = [self._filter_status_line(), ""]
        lines.extend([_ranking_header_line(), _ranking_separator_line()])
        lines.extend(
            _ranking_line(
                row,
                selected=index == self.selection_index,
            )
            for index, row in visible_rows
        )
        selected = rows[self.selection_index]
        lines.extend(["", self._selected_pick_preview_line(selected), ""])
        lines.extend(self._selected_player_detail_lines(selected))
        return lines

    def _visible_rankings(self, *, visible_count: int) -> list[tuple[int, RankingRow]]:
        rows = self.selectable_rankings()
        if not rows or visible_count <= 0:
            return []

        self._sync_ranking_scroll(visible_count=visible_count)
        start = self.ranking_scroll_offset
        end = min(start + visible_count, len(rows))
        return list(enumerate(rows[start:end], start=start))

    def _sync_ranking_scroll(self, *, visible_count: int) -> None:
        rows = self.selectable_rankings()
        if not rows or visible_count <= 0:
            self.ranking_scroll_offset = 0
            return

        max_offset = max(len(rows) - visible_count, 0)
        self.ranking_scroll_offset = max(0, min(self.ranking_scroll_offset, max_offset))

        if self.selection_index < self.ranking_scroll_offset:
            self.ranking_scroll_offset = self.selection_index
        elif self.selection_index >= self.ranking_scroll_offset + visible_count:
            self.ranking_scroll_offset = self.selection_index - visible_count + 1

        self.ranking_scroll_offset = max(0, min(self.ranking_scroll_offset, max_offset))

    def _selected_ranking_player_id(self) -> str | None:
        rows = self.selectable_rankings()
        if not rows:
            return None
        return rows[min(self.selection_index, len(rows) - 1)].player_id

    def _restore_selection(self, player_id: str | None) -> None:
        rows = self.selectable_rankings()
        if player_id is not None:
            for index, row in enumerate(rows):
                if row.player_id == player_id:
                    self.selection_index = index
                    self._sync_ranking_scroll(visible_count=30)
                    return
        self.selection_index = 0
        self.ranking_scroll_offset = 0

    def _search_status_message(self) -> str:
        if not self.search_query:
            return "Search cleared."
        match_count = len(self.selectable_rankings())
        noun = "match" if match_count == 1 else "matches"
        return f"Search: {self.search_query} ({match_count} {noun})"

    def _recommendation_lines(self) -> list[str]:
        recommendation = self.recommendation()
        if recommendation is None:
            return ["No recommendations are available."]
        rows = [recommendation.primary, *recommendation.alternatives]
        lines = [
            "Top 5 by positions you still need",
            "These groups come from your current roster vacancies and update after every pick.",
            "",
            *self._positional_recommendation_lines(),
            "",
            *self._rollout_recommendation_lines(recommendation.primary.player_id),
            "",
            "Best overall recommendation",
            "Scores combine VORP, starter need, tier, ADP value, availability, and penalties.",
            "",
        ]
        for row in rows:
            lines.append(self._recommendation_score_line(row, include_rank=True))
            lines.append(f"     {self._recommendation_breakdown_line(row)}")
            lines.extend(f"     - {item}" for item in row.explanation)
            lines.append("")
        return lines

    def _positional_recommendation_lines(self) -> list[str]:
        lines: list[str] = []
        for group in self.positional_recommendations():
            lines.append(f"{group.position} need={group.remaining_need}")
            if not group.candidates:
                lines.append("     No available candidates.")
                lines.append("")
                continue
            for index, score in enumerate(group.candidates, start=1):
                ranking = self._ranking_by_id(score.player_id)
                name = ranking.full_name if ranking else score.player_id
                tier = "-" if ranking is None else str(ranking.tier)
                projected = "-" if ranking is None else f"{ranking.projected_points:.1f}"
                lines.append(
                    f"  {index}. {name:<26} score={score.total_score:>6.1f} "
                    f"proj={projected:>6} tier={tier:<2}"
                )
            lines.append("")
        if not lines:
            lines.append("No open starter or flex needs remain.")
        return lines

    def _rollout_recommendation_lines(self, baseline_player_id: str) -> list[str]:
        rollout = self.rollout_recommendation()
        if rollout is None:
            return [
                "Best path rollout",
                "Available when your team is on clock.",
            ]

        lines = [
            "Best path rollout",
            "Simulates candidate picks and ranks the resulting roster paths.",
            "",
        ]
        for index, candidate in enumerate([rollout.primary, *rollout.alternatives], start=1):
            ranking = self._ranking_by_id(candidate.player_id)
            name = ranking.full_name if ranking else candidate.player_id
            marker = (
                "same as best-now"
                if candidate.player_id == baseline_player_id
                else "path pick"
            )
            lines.append(
                f"{index}. {name:<26} score={candidate.optimizer_score:>7.1f} {marker}"
            )
            lines.append(
                f"   avg_vorp={candidate.average_vorp:.1f} "
                f"downside={candidate.downside_vorp:.1f} "
                f"vol={candidate.vorp_volatility:.1f} "
                f"balance={candidate.roster_balance_score:.1f} "
                f"current={candidate.current_pick_score:.1f}"
            )
            lines.append(f"   {self._next_pick_options_text(candidate.next_pick_position_options)}")
            lines.extend(f"   - {item}" for item in candidate.explanation[:3])
            lines.append("")
        return lines

    def _best_overall_recommendation_lines(self, *, include_header: bool) -> list[str]:
        recommendation = self.recommendation()
        if recommendation is None:
            if include_header:
                return ["Best overall recommendation", "No recommendation available."]
            return ["No recommendation available."]

        primary = recommendation.primary
        lines: list[str] = []
        if include_header:
            lines.extend(
                [
                    "Best overall recommendation",
                    (
                        "Adjusted for your current roster, open needs, player value, "
                        "tier, ADP, and availability."
                    ),
                ]
            )
        lines.extend(
            [
                self._recommendation_score_line(primary, include_rank=False),
                self._recommendation_breakdown_line(primary),
                f"Availability before next pick: {primary.next_pick_availability:.0%}",
                "",
                *self._rollout_summary_lines(primary.player_id),
                "Why:",
                *[f"- {item}" for item in primary.explanation[:4]],
            ]
        )
        return lines

    def _rollout_summary_lines(self, baseline_player_id: str) -> list[str]:
        rollout = self.rollout_recommendation()
        if rollout is None:
            return ["Best path: available when your team is on clock.", ""]

        primary = rollout.primary
        ranking = self._ranking_by_id(primary.player_id)
        name = ranking.full_name if ranking else primary.player_id
        comparison = (
            "matches best-now pick"
            if primary.player_id == baseline_player_id
            else "differs from best-now pick"
        )
        return [
            f"Best path: {name} score={primary.optimizer_score:.1f} ({comparison})",
            (
                f"Rollout: avg VORP {primary.average_vorp:.1f} | "
                f"downside {primary.downside_vorp:.1f} | "
                f"vol {primary.vorp_volatility:.1f}"
            ),
            self._next_pick_options_text(primary.next_pick_position_options),
            "",
        ]

    def _next_pick_options_text(self, options: dict[str, float]) -> str:
        if not options:
            return "Next pick options: no ranked options projected"
        parts = [f"{position} {count:.1f}" for position, count in sorted(options.items())]
        return "Next pick options: " + ", ".join(parts)

    def _recommendation_score_line(
        self,
        recommendation: RecommendationScore,
        *,
        include_rank: bool,
    ) -> str:
        ranking = self._ranking_by_id(recommendation.player_id)
        name = ranking.full_name if ranking else recommendation.player_id
        position = "-" if ranking is None else ranking.position.value
        prefix = f"{recommendation.rank:>3}. " if include_rank else "Best overall: "
        return (
            f"{prefix}{name} ({position}) score={recommendation.total_score:.1f} "
            f"phase={recommendation.draft_phase}"
        )

    def _recommendation_breakdown_line(self, recommendation: RecommendationScore) -> str:
        return (
            f"Breakdown: need {recommendation.need_score:+.1f} | "
            f"value {recommendation.value_score:+.1f} | tier {recommendation.tier_score:+.1f} | "
            f"drop {recommendation.tier_drop_score:+.1f} | "
            f"risk {recommendation.next_pick_risk_score:+.1f} | "
            f"market {recommendation.market_score:+.1f} | "
            f"penalty {-recommendation.penalty:+.1f}"
        )

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
        selected_points, selected_vorp = self._manager_roster_totals(selected_manager_id)
        lines = [
            "Managers",
            "Use up/down to inspect roster strength as picks come in.",
            "",
            f"{'Team':<16} {'Picks':>5} {'Proj':>8} {'VORP':>8} Roster",
            "-" * 70,
        ]
        for index, manager in enumerate(self.state.league_config.draft_order):
            roster = self.state.rosters[manager.id]
            projected_points, vorp = self._manager_roster_totals(manager.id)
            marker = ">" if index == self.manager_selection_index else " "
            on_clock = "*" if manager.id == self.state.manager_on_clock else " "
            user = "YOU" if manager.id == self.state.league_config.league.user_manager_id else "   "
            lines.append(
                f"{marker}{on_clock} {self._manager_label(manager.id):<12} {user} "
                f"{len(roster.player_ids):>5} {projected_points:>8.1f} {vorp:>8.1f} "
                f"{self._position_count_text(roster.positional_counts)}"
            )
        lines.extend(
            [
                "",
                f"Roster: {self._manager_label(selected_manager_id)}",
                f"Team totals: projected={selected_points:.1f} VORP={selected_vorp:.1f}",
            ]
        )
        if not selected_roster.player_ids:
            lines.append("No picks yet.")
        else:
            for player_id in selected_roster.player_ids:
                player = self.state.players[player_id]
                ranking = self._ranking_by_id(player_id)
                projected_points = 0 if ranking is None else ranking.projected_points
                vorp = 0 if ranking is None else ranking.vorp
                lines.append(
                    f"{self._team_badge(player.nfl_team_id)} {player.position:<3} "
                    f"{player.full_name:<26} proj={projected_points:>6.1f} "
                    f"vorp={vorp:>6.1f}"
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
        cache_key = self._path_analysis_key()
        if self._path_analysis_cache_key != cache_key or self._path_analysis_cache is None:
            return [
                "Multi-path draft analysis",
                "",
                "Press a to run simulated draft paths from the current board.",
                "The log below updates as paths finish.",
                "",
                "Run Log",
                *self.path_analysis_logs[-18:],
            ]

        league_result, strategy_result = self._path_analysis_cache
        return [
            *self._simulation_result_lines(league_result, strategy_result),
            "",
            "Run Log",
            *self.path_analysis_logs[-12:],
        ]

    def _simulation_result_lines(
        self,
        league_result: LeaguePathAnalysisResult,
        strategy_result: StrategyPathAnalysisResult,
    ) -> list[str]:
        lines = [
            f"After {league_result.simulation_count} simulated draft paths:",
            "",
            "Manager Results (ranked by avg finish)",
        ]
        for index, manager in enumerate(league_result.manager_results[:8], start=1):
            lines.append(
                f"{index}. {self._manager_label(manager.manager_id):<12} "
                f"avg VORP {manager.average_vorp:>7.1f}   "
                f"avg pts {manager.average_projected_points:>7.1f}   "
                f"avg finish {manager.average_finish:>4.1f}"
            )
        lines.extend(["", "Draft Strategy Analysis"])
        if not strategy_result.paths:
            lines.append("No future user pick is available to test.")
        else:
            for path in strategy_result.paths:
                lines.append(
                    f"{path.label:<18} avg VORP {path.average_vorp:>7.1f}   "
                    f"avg pts {path.average_projected_points:>7.1f}   "
                    f"top3 {path.top_three_rate:>5.0%}   "
                    f"target {path.forced_player_name}"
                )

        risk = league_result.user_risk
        lines.extend(
            [
                "",
                "Risk",
                f"Best case: {risk.best_case_vorp:>7.1f} VORP",
                f"Median:    {risk.median_vorp:>7.1f} VORP",
                f"Worst:     {risk.worst_case_vorp:>7.1f} VORP",
                f"Volatility:{risk.vorp_volatility:>7.1f}",
                f"Top 3 rate:{risk.top_three_rate:>7.0%}",
                f"Win rate:  {risk.first_place_rate:>7.0%}",
            ]
        )
        return lines

    def run_path_analysis(
        self,
        *,
        progress_callback: LeaguePathProgressCallback | None = None,
        strategy_progress_callback: StrategyPathProgressCallback | None = None,
    ) -> tuple[LeaguePathAnalysisResult, StrategyPathAnalysisResult]:
        self._invalidate_path_analysis()
        self.path_analysis_logs = ["Starting league path analysis..."]
        cache_key = self._path_analysis_key()
        result = self._path_analysis(
            progress_callback=progress_callback,
            strategy_progress_callback=strategy_progress_callback,
        )
        self._path_analysis_cache_key = cache_key
        self._path_analysis_cache = result
        self.path_analysis_logs.append("Finished path analysis.")
        self.status_message = "Path analysis complete."
        return result

    def _path_analysis(
        self,
        *,
        progress_callback: LeaguePathProgressCallback | None = None,
        strategy_progress_callback: StrategyPathProgressCallback | None = None,
    ) -> tuple[LeaguePathAnalysisResult, StrategyPathAnalysisResult]:
        cache_key = self._path_analysis_key()
        if self._path_analysis_cache_key == cache_key and self._path_analysis_cache is not None:
            return self._path_analysis_cache

        draft_config = DraftSimulationConfig(
            simulation_count=40,
            seed=71,
            candidate_limit=max(len(self._rankings), 1),
        )
        league_result = analyze_league_paths(
            self.state,
            self._rankings,
            config=LeaguePathSimulationConfig(
                simulation_count=40,
                seed=71,
                draft_config=draft_config,
            ),
            progress_callback=progress_callback,
        )
        self.path_analysis_logs.append(
            "Sampling boards at your next pick and comparing RB/WR/QB/TE paths..."
        )
        strategy_result = analyze_user_strategy_paths(
            self.state,
            self._rankings,
            config=StrategyPathSimulationConfig(
                simulation_count=12,
                seed=211,
                draft_config=draft_config,
            ),
            progress_callback=strategy_progress_callback,
        )
        return league_result, strategy_result

    def _path_analysis_key(self) -> tuple[str, ...]:
        return tuple(pick.player_id for pick in self.state.completed_picks)

    def _invalidate_path_analysis(self) -> None:
        had_analysis = self._path_analysis_cache is not None
        self._path_analysis_cache_key = None
        self._path_analysis_cache = None
        if had_analysis:
            self.path_analysis_logs = ["Board changed. Press a to rerun path analysis."]

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

    def _manager_roster_totals(self, manager_id: str) -> tuple[float, float]:
        roster = self.state.rosters[manager_id]
        projected_points = 0.0
        vorp = 0.0
        for player_id in roster.player_ids:
            ranking = self._ranking_by_id(player_id)
            if ranking is None:
                continue
            projected_points += ranking.projected_points
            vorp += ranking.vorp
        return round(projected_points, 1), round(vorp, 1)

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

    def _selected_pick_preview_line(self, ranking: RankingRow) -> str:
        summary = summarize_draft_state(self.state)
        return (
            f"Confirm pick {summary.current_overall_pick}: "
            f"{summary.manager_on_clock} drafts {ranking.full_name} "
            f"({ranking.position.value}, {ranking.nfl_team_id or 'FA'})"
        )

    def _filter_status_line(self) -> str:
        match_count = len(self.selectable_rankings())
        return (
            f"Filters: position={self.position_filter} search={self.search_query or '-'} "
            f"matches={match_count} | [ ] cycle positions, c clear"
        )


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
            if controller.search_active:
                controller.finish_search()
                continue
            return
        if controller.search_active:
            _handle_live_search_key(controller, key)
            continue
        if key in {curses.KEY_RIGHT, ord("\t")}:
            controller.move_view(1)
        elif key == curses.KEY_LEFT:
            controller.move_view(-1)
        elif key == curses.KEY_DOWN:
            controller.move_selection(1)
        elif key == curses.KEY_UP:
            controller.move_selection(-1)
        elif key == curses.KEY_NPAGE:
            controller.page_selection(1)
        elif key == curses.KEY_PPAGE:
            controller.page_selection(-1)
        elif key == curses.KEY_HOME:
            controller.jump_selection(to_end=False)
        elif key == curses.KEY_END:
            controller.jump_selection(to_end=True)
        elif key in {ord("\n"), ord("\r"), ord("d")}:
            controller.draft_selected_player()
        elif key == ord("u"):
            controller.undo()
        elif key == ord("r"):
            controller.redo()
        elif key == ord("s"):
            controller.save()
        elif key == ord("a") and controller.current_view == "Simulation":
            _run_path_analysis_interactive(screen, controller)
        elif key == ord("c"):
            controller.set_search("")
            controller.set_position_filter("ALL")
            controller.search_active = False
        elif key == ord("["):
            controller.cycle_position_filter(-1)
        elif key == ord("]"):
            controller.cycle_position_filter(1)
        elif key in {ord("1"), ord("2"), ord("3"), ord("4"), ord("5"), ord("6")}:
            controller.set_position_filter(POSITIONS[int(chr(key)) - 1])
        elif key == ord("0"):
            controller.set_position_filter("ALL")
        elif key == ord("/"):
            controller.start_search()


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


def _handle_live_search_key(controller: CliDraftController, key: int) -> None:
    if key in {ord("\n"), ord("\r"), 27}:
        controller.finish_search()
        return
    if key in {curses.KEY_BACKSPACE, 127, 8}:
        controller.backspace_search()
        return
    if 0 <= key <= 255:
        controller.append_search_character(chr(key))


def _run_path_analysis_interactive(
    screen: curses.window,
    controller: CliDraftController,
) -> None:
    def league_progress(progress: LeaguePathProgress) -> None:
        leader = controller._manager_label(progress.current_leader_id)
        controller.path_analysis_logs.append(
            f"path {progress.completed_paths:>2}/{progress.total_paths} "
            f"seed={progress.seed} leader={leader} "
            f"vorp={progress.current_leader_vorp:.1f} "
            f"status={progress.stopped_reason}"
        )
        controller.status_message = (
            f"Running path analysis {progress.completed_paths}/{progress.total_paths}..."
        )
        _draw(screen, controller)

    def strategy_progress(progress: StrategyPathProgress) -> None:
        target = progress.forced_player_name or "no candidate"
        controller.path_analysis_logs.append(
            f"strategy {progress.completed_paths:>2}/{progress.total_paths} "
            f"board={progress.board_sample} pos={progress.position} target={target}"
        )
        controller.status_message = (
            f"Testing draft strategies {progress.completed_paths}/{progress.total_paths}..."
        )
        _draw(screen, controller)

    controller.status_message = "Running path analysis..."
    controller.run_path_analysis(
        progress_callback=league_progress,
        strategy_progress_callback=strategy_progress,
    )
    _draw(screen, controller)


def _draw_header(screen: curses.window, controller: CliDraftController, width: int) -> None:
    summary = summarize_draft_state(controller.state)
    brand = " bayesiandraft@draft-room % bayesiandraft "
    status = (
        f"Version {__version__}  "
        f"Pick {summary.current_overall_pick}/{controller.state.total_picks}  "
        f"Round {controller.state.current_round or '-'}  Clock {summary.manager_on_clock}"
    )
    _safe_addnstr(screen, 0, 0, brand.ljust(width), width, curses.color_pair(3) | curses.A_BOLD)
    _safe_addnstr(screen, 1, 2, status.ljust(max(width - 2, 1)), max(width - 2, 1), curses.A_BOLD)
    progress = _progress_bar(summary.completed_pick_count, controller.state.total_picks, width - 24)
    _safe_addnstr(
        screen,
        2,
        2,
        (
            f"Draft progress {progress} {summary.available_player_count} available  "
            f"Next user {summary.next_user_pick or '-'}"
        ).ljust(max(width - 2, 1)),
        max(width - 2, 1),
        curses.color_pair(5),
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
    body_height = max(height - 10, 1)
    if controller.current_view == "Summary" and width >= 108:
        _draw_summary_workspace(screen, controller, top, 0, body_height, width)
        return
    if controller.current_view == "Rankings" and width >= 104:
        _draw_rankings_workspace(screen, controller, top, 0, body_height, width)
        return
    if controller.current_view == "Managers" and width >= 96:
        _draw_manager_workspace(screen, controller, top, 0, body_height, width)
        return

    _draw_box(screen, top, 0, body_height, width, controller.current_view)
    if controller.current_view == "Summary":
        _draw_summary_lines(
            screen,
            controller.view_lines(),
            top + 1,
            3,
            body_height - 2,
            width - 6,
        )
    else:
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
    prompt = _footer_prompt(controller)
    _safe_addnstr(screen, height - 3, 0, (" " + prompt).ljust(width), width, curses.color_pair(6))
    _safe_addnstr(screen, height - 2, 0, (" " + "-" * max(width - 2, 0)).ljust(width), width)
    _safe_addnstr(
        screen,
        height - 1,
        1,
        controller.status_message,
        max(width - 2, 1),
        curses.color_pair(5),
    )


def _progress_bar(completed: int, total: int, width: int) -> str:
    bar_width = max(min(width, 40), 8)
    filled = 0 if total == 0 else round((completed / total) * bar_width)
    return "[" + "#" * filled + "." * (bar_width - filled) + "]"


def _footer_prompt(controller: CliDraftController) -> str:
    search = controller.search_query or "none"
    mode = "SEARCH" if controller.search_active else controller.current_view.lower()
    matches = len(controller.selectable_rankings())
    action = "a analyze  " if controller.current_view == "Simulation" else ""
    return (
        f"~/BayesianDraft  mode={mode}  filter={search}  "
        f"matches={matches}  pos={controller.position_filter}  "
        f"{action}enter/d draft  / search  [ ] position  q quit"
    )


def _draw_summary_workspace(
    screen: curses.window,
    controller: CliDraftController,
    y: int,
    x: int,
    height: int,
    width: int,
) -> None:
    left_width = 34
    right_width = 38
    center_width = width - left_width - right_width - 2
    summary = summarize_draft_state(controller.state)
    user_manager_id = controller.state.league_config.league.user_manager_id
    user_roster = controller.state.rosters[user_manager_id]

    _draw_box(screen, y, x, height, left_width, "Status")
    status_lines = [
        "BayesianDraft",
        *COMPACT_LOGO_LINES,
        "",
        f"v{__version__}",
        f"Snapshot: {controller.snapshot.snapshot.snapshot_id}",
        "",
        "CURRENT PICK",
        f">>> {summary.current_overall_pick}/{controller.state.total_picks} <<<",
        f"Round: {controller.state.current_round or '-'}",
        f"Clock: {summary.manager_on_clock}",
        f"Next user: {summary.next_user_pick or '-'}",
        f"Available: {summary.available_player_count}",
        controller.last_save_message,
    ]
    _draw_summary_lines(screen, status_lines, y + 1, x + 2, height - 2, left_width - 4)

    center_x = x + left_width + 1
    _draw_box(screen, y, center_x, height, center_width, "Decision")
    decision_lines = [
        *controller._best_overall_recommendation_lines(include_header=True),
        "",
        "Enter every pick as it happens; this updates after each pick.",
    ]
    _draw_decision_lines(
        screen,
        decision_lines,
        y + 1,
        center_x + 2,
        height - 2,
        center_width - 4,
    )

    right_x = center_x + center_width + 1
    top_height = max(height // 2, 7)
    bottom_height = height - top_height - 1
    _draw_box(screen, y, right_x, top_height, right_width, "Your Roster")
    roster_lines = [f"Picks: {len(user_roster.player_ids)}"]
    roster_lines.append(controller._position_count_text(user_roster.positional_counts))
    roster_lines.append("")
    if user_roster.player_ids:
        for player_id in user_roster.player_ids[-8:]:
            player = controller.state.players[player_id]
            roster_lines.append(f"{player.position:<3} {player.full_name}")
    else:
        roster_lines.append("No picks yet.")
    _draw_lines(screen, roster_lines, y + 1, right_x + 2, top_height - 2, right_width - 4)

    recent_y = y + top_height + 1
    _draw_box(screen, recent_y, right_x, bottom_height, right_width, "Recent Picks")
    pick_lines = []
    for pick in controller.state.completed_picks[-8:]:
        player = controller.state.players[pick.player_id]
        pick_lines.append(f"{pick.overall_pick:>3} {pick.manager_id:<10} {player.full_name}")
    if not pick_lines:
        pick_lines.append("No picks recorded.")
    _draw_lines(screen, pick_lines, recent_y + 1, right_x + 2, bottom_height - 2, right_width - 4)


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
        _safe_addnstr(screen, y, x + 2, label, width - 4, curses.color_pair(4) | curses.A_BOLD)


def _draw_summary_lines(
    screen: curses.window,
    lines: list[str],
    y: int,
    x: int,
    max_lines: int,
    width: int,
) -> None:
    for offset, line in enumerate(lines[:max_lines]):
        attrs = _summary_line_attrs(line)
        _safe_addnstr(screen, y + offset, x, line, width, attrs)


def _summary_line_attrs(line: str) -> int:
    if line.startswith("BayesianDraft"):
        return curses.color_pair(3) | curses.A_BOLD
    if line in COMPACT_LOGO_LINES:
        return curses.color_pair(1) | curses.A_BOLD
    if line.startswith("Version") or line.startswith("v"):
        return curses.color_pair(6) | curses.A_BOLD
    if line == "CURRENT PICK":
        return curses.color_pair(4) | curses.A_BOLD
    if line.startswith(">>>"):
        return curses.color_pair(5) | curses.A_BOLD | curses.A_REVERSE
    if line.startswith("Pick") or line.startswith("Clock") or line.startswith("Next"):
        return curses.color_pair(5) | curses.A_BOLD
    return 0


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


def _draw_decision_lines(
    screen: curses.window,
    lines: list[str],
    y: int,
    x: int,
    max_lines: int,
    width: int,
) -> None:
    for offset, line in enumerate(lines[:max_lines]):
        attrs = _decision_line_attrs(line)
        _safe_addnstr(screen, y + offset, x, line, width, attrs)


def _decision_line_attrs(line: str) -> int:
    if line == "Best overall recommendation":
        return curses.color_pair(4) | curses.A_BOLD
    if line.startswith("Best overall:"):
        return curses.color_pair(5) | curses.A_BOLD | curses.A_REVERSE
    if line.startswith("Availability before next pick:"):
        return curses.color_pair(6) | curses.A_BOLD
    if line == "Why:":
        return curses.A_BOLD
    return 0


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
    if rows:
        row_limit = max(height - 4, 0)
        visible_rows = controller._visible_rankings(visible_count=row_limit)
        ranking_lines = [
            _ranking_header_line(),
            _ranking_separator_line(),
            *[
                _ranking_line(row, selected=index == controller.selection_index)
                for index, row in visible_rows
            ],
        ]
    else:
        ranking_lines = ["No available players match the current filter."]
    _draw_lines(screen, ranking_lines, y + 1, x + 2, height - 2, left_width - 4)

    _draw_box(screen, y, x + left_width + 1, height, right_width, "Player Detail")
    detail_lines = (
        ["No player selected."]
        if selected is None
        else [
            f"{controller._team_badge(selected.nfl_team_id)} {selected.full_name}",
            controller._selected_pick_preview_line(selected),
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
    selected_points, selected_vorp = controller._manager_roster_totals(selected_manager_id)

    _draw_box(screen, y, x, height, left_width, "Managers")
    manager_lines = [f"{'Team':<14} {'Pk':>2} {'Proj':>7} {'VORP':>7}"]
    for index, manager in enumerate(controller.state.league_config.draft_order):
        roster = controller.state.rosters[manager.id]
        projected_points, vorp = controller._manager_roster_totals(manager.id)
        marker = ">" if index == controller.manager_selection_index else " "
        clock = "*" if manager.id == controller.state.manager_on_clock else " "
        user = (
            "YOU"
            if manager.id == controller.state.league_config.league.user_manager_id
            else "   "
        )
        manager_lines.append(
            f"{marker}{clock} {controller._manager_label(manager.id):<12} "
            f"{user} {len(roster.player_ids):>2} {projected_points:>7.1f} {vorp:>7.1f}"
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
        f"Totals: projected={selected_points:.1f} VORP={selected_vorp:.1f}",
        controller._position_count_text(selected_roster.positional_counts),
        "",
    ]
    if not selected_roster.player_ids:
        roster_lines.append("No picks yet.")
    else:
        for player_id in selected_roster.player_ids:
            player = controller.state.players[player_id]
            ranking = controller._ranking_by_id(player_id)
            projected_points = 0 if ranking is None else ranking.projected_points
            vorp = 0 if ranking is None else ranking.vorp
            roster_lines.append(
                f"{controller._team_badge(player.nfl_team_id)} {player.position:<3} "
                f"{player.full_name:<24} {projected_points:>6.1f} {vorp:>6.1f}"
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
        curses.init_pair(4, curses.COLOR_BLUE, -1)
        curses.init_pair(5, curses.COLOR_GREEN, -1)
        curses.init_pair(6, curses.COLOR_WHITE, -1)
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
    adp_delta = "-" if row.adp_delta is None else f"{row.adp_delta:+.1f}"
    return (
        f"{marker} {row.overall_rank:>4}  {row.full_name:<28} {row.position.value:<3} "
        f"{row.tier:>4} {row.projected_points:>7.1f} {row.vorp:>7.1f} "
        f"{row.adp or 0:>7.1f} {adp_delta:>7}"
    )


def _ranking_header_line() -> str:
    return (
        f"  {'Rank':>4}  {'Player':<28} {'Pos':<3} {'Tier':>4} "
        f"{'Proj':>7} {'VORP':>7} {'ADP':>7} {'ADPΔ':>7}"
    )


def _ranking_separator_line() -> str:
    return "  " + "-" * (len(_ranking_header_line()) - 2)

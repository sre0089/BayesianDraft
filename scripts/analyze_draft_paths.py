from argparse import ArgumentParser
from pathlib import Path

from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import RankingRow, build_baseline_rankings
from bayesiandraft.simulation import (
    LeaguePathAnalysisResult,
    LeaguePathSimulationConfig,
    StrategyPathAnalysisResult,
    StrategyPathSimulationConfig,
    analyze_league_paths,
    analyze_user_strategy_paths,
)
from bayesiandraft.simulation.draft import DraftSimulationConfig
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


def main() -> None:
    parser = ArgumentParser(description="Analyze many possible BayesianDraft paths.")
    add_snapshot_argument(parser)
    parser.add_argument("--draft-state", help="Optional saved draft state JSON to analyze.")
    parser.add_argument("--simulations", type=int, default=500)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--candidate-limit", type=int, default=250)
    parser.add_argument(
        "--auto-pick-to-user",
        action="store_true",
        help="Auto-draft from a fresh snapshot until the configured user manager is on clock.",
    )
    args = parser.parse_args()

    snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    if args.draft_state:
        state = DraftState.load(Path(args.draft_state))
    elif args.auto_pick_to_user:
        state = _auto_pick_to_user(state, build_baseline_rankings(snapshot))

    rankings = build_baseline_rankings(snapshot)
    draft_config = DraftSimulationConfig(
        simulation_count=args.simulations,
        seed=args.seed,
        candidate_limit=args.candidate_limit,
    )
    league_result = analyze_league_paths(
        state,
        rankings,
        config=LeaguePathSimulationConfig(
            simulation_count=args.simulations,
            seed=args.seed,
            draft_config=draft_config,
        ),
    )
    strategy_result = analyze_user_strategy_paths(
        state,
        rankings,
        config=StrategyPathSimulationConfig(
            simulation_count=max(args.simulations // 4, 1),
            seed=args.seed + args.simulations,
            draft_config=draft_config,
        ),
    )

    print(
        format_draft_path_report(
            league_result,
            strategy_result,
            user_manager_id=state.league_config.league.user_manager_id,
        )
    )


def format_draft_path_report(
    league_result: LeaguePathAnalysisResult,
    strategy_result: StrategyPathAnalysisResult,
    *,
    user_manager_id: str,
) -> str:
    lines = [f"After {league_result.simulation_count} simulated draft paths:", ""]
    lines.append("Manager Results")
    for index, manager in enumerate(league_result.manager_results[:8], start=1):
        label = _manager_label(manager.manager_id, user_manager_id)
        lines.append(
            f"{index}. {label:<12} avg VORP {manager.average_vorp:>7.1f}   "
            f"avg pts {manager.average_projected_points:>7.1f}   "
            f"avg finish {manager.average_finish:>4.1f}"
        )
    lines.append("")
    lines.append("Your Strategy Outcomes")
    if not strategy_result.paths:
        lines.append("Available when your team is currently on clock.")
    else:
        for path in strategy_result.paths:
            lines.append(
                f"{path.label:<18} avg VORP {path.average_vorp:>7.1f}   "
                f"avg pts {path.average_projected_points:>7.1f}   "
                f"top3 {path.top_three_rate:>5.0%}"
            )
    lines.append("")
    lines.append("Risk")
    risk = league_result.user_risk
    lines.append(f"Best case: {risk.best_case_vorp:>7.1f} VORP")
    lines.append(f"Median:    {risk.median_vorp:>7.1f} VORP")
    lines.append(f"Worst:     {risk.worst_case_vorp:>7.1f} VORP")
    lines.append(f"Volatility:{risk.vorp_volatility:>7.1f}")
    lines.append(f"Top 3 rate:{risk.top_three_rate:>7.0%}")
    lines.append(f"Win rate:  {risk.first_place_rate:>7.0%}")
    return "\n".join(lines)


def _auto_pick_to_user(state: DraftState, rankings: list[RankingRow]) -> DraftState:
    while (
        state.manager_on_clock != state.league_config.league.user_manager_id
        and not state.is_complete
    ):
        available_ids = set(state.available_player_ids)
        selected = next(
            ranking.player_id for ranking in rankings if ranking.player_id in available_ids
        )
        state = state.record_pick(selected)
    return state


def _manager_label(manager_id: str, user_manager_id: str) -> str:
    if manager_id == user_manager_id:
        return "Your Team"
    return manager_id.replace("manager_", "Team ")


if __name__ == "__main__":
    main()

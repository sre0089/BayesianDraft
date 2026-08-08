import random
from argparse import ArgumentParser
from dataclasses import dataclass

from bayesiandraft.draft import DraftState, build_roster_balance_report
from bayesiandraft.rankings import RankingRow, build_baseline_rankings
from bayesiandraft.recommendations import recommend_players
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


@dataclass(frozen=True)
class DraftAuditResult:
    seed: int
    complete: bool
    roster_size: int
    counts: dict[str, int]
    missing: dict[str, int]
    user_pick_names: list[str]
    stopped_reason: str


def main() -> None:
    parser = ArgumentParser(
        description=(
            "Audit whether blindly following BayesianDraft recommendations "
            "can finish a legal roster across sampled drafts."
        )
    )
    add_snapshot_argument(parser)
    parser.add_argument("--drafts", type=int, default=25)
    parser.add_argument("--seed", type=int, default=91)
    parser.add_argument("--candidate-limit", type=int, default=250)
    args = parser.parse_args()

    snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    rankings = build_baseline_rankings(snapshot)
    results = audit_recommended_drafts(
        state,
        rankings,
        drafts=args.drafts,
        seed=args.seed,
        candidate_limit=args.candidate_limit,
    )
    print(format_audit_report(results))


def audit_recommended_drafts(
    initial_state: DraftState,
    rankings: list[RankingRow],
    *,
    drafts: int,
    seed: int,
    candidate_limit: int,
) -> list[DraftAuditResult]:
    return [
        _run_audit_draft(
            initial_state,
            rankings,
            seed=seed + offset,
            candidate_limit=candidate_limit,
        )
        for offset in range(drafts)
    ]


def format_audit_report(results: list[DraftAuditResult]) -> str:
    complete_count = sum(result.complete for result in results)
    lines = [
        f"Model roster completion audit: {complete_count}/{len(results)} complete",
        "",
        "Draft Results",
    ]
    for result in results:
        status = "PASS" if result.complete else "FAIL"
        missing = _format_missing(result.missing)
        counts = " ".join(
            f"{position}:{count}" for position, count in sorted(result.counts.items())
        )
        lines.append(
            f"{status} seed={result.seed:<4} roster={result.roster_size:<2} "
            f"missing={missing:<20} stop={result.stopped_reason:<18} counts={counts}"
        )
    if results:
        first = results[0]
        lines.extend(
            [
                "",
                "Example followed-pick path",
                *[f"- {name}" for name in first.user_pick_names],
            ]
        )
    return "\n".join(lines)


def _run_audit_draft(
    initial_state: DraftState,
    rankings: list[RankingRow],
    *,
    seed: int,
    candidate_limit: int,
) -> DraftAuditResult:
    rng = random.Random(seed)
    state = initial_state
    user_manager_id = state.league_config.league.user_manager_id
    stopped_reason = "draft_complete"

    while not state.is_complete:
        if state.manager_on_clock == user_manager_id:
            try:
                selected_player_id = recommend_players(state, rankings).primary.player_id
            except ValueError:
                stopped_reason = "no_recommendation"
                break
        else:
            opponent_pick = _sample_opponent_pick_or_none(
                state,
                rankings,
                rng=rng,
                candidate_limit=candidate_limit,
            )
            if opponent_pick is None:
                stopped_reason = "no_ranked_players"
                break
            selected_player_id = opponent_pick
        state = state.record_pick(selected_player_id)

    user_roster = state.rosters[user_manager_id]
    report = build_roster_balance_report(state, user_manager_id)
    missing = {
        position.position: position.remaining_starter_need
        for position in report.positions
        if position.remaining_starter_need > 0
    }
    user_pick_names = [state.players[player_id].full_name for player_id in user_roster.player_ids]
    return DraftAuditResult(
        seed=seed,
        complete=not missing,
        roster_size=len(user_roster.player_ids),
        counts=user_roster.positional_counts,
        missing=missing,
        user_pick_names=user_pick_names,
        stopped_reason=stopped_reason,
    )


def _sample_opponent_pick_or_none(
    state: DraftState,
    rankings: list[RankingRow],
    *,
    rng: random.Random,
    candidate_limit: int,
) -> str | None:
    available = [
        ranking
        for ranking in rankings
        if ranking.player_id in state.available_player_ids
    ][:candidate_limit]
    if not available:
        return None

    manager_id = state.manager_on_clock
    weights = []
    for ranking in available:
        weights.append(
            max(
                (1 / ranking.overall_rank)
                + max(ranking.vorp, 0) / 100
                + _opponent_need_bonus(state, manager_id, ranking),
                0.001,
            )
        )
    return rng.choices([ranking.player_id for ranking in available], weights=weights, k=1)[0]


def _opponent_need_bonus(
    state: DraftState,
    manager_id: str | None,
    ranking: RankingRow,
) -> float:
    if manager_id is None:
        return 0
    roster = state.rosters[manager_id]
    current_count = roster.positional_counts.get(ranking.position.value, 0)
    starter_target = state.league_config.roster.starting_slots.get(ranking.position.value, 0)
    return 0.4 if current_count < starter_target else 0


def _format_missing(missing: dict[str, int]) -> str:
    if not missing:
        return "none"
    return ",".join(f"{position}:{count}" for position, count in sorted(missing.items()))


if __name__ == "__main__":
    main()

from argparse import ArgumentParser
from dataclasses import dataclass
from time import perf_counter

from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.rankings.baseline import RankingRow
from bayesiandraft.recommendations import build_path_bank_context, recommend_players
from bayesiandraft.simulation import DraftPathBank
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


def main() -> None:
    parser = ArgumentParser(description="Audit fast path-bank recommendation latency.")
    add_snapshot_argument(parser)
    parser.add_argument("--path-bank", required=True)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--budget-ms", type=float, default=100)
    args = parser.parse_args()

    snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    rankings = build_baseline_rankings(snapshot)
    path_bank = DraftPathBank.load(args.path_bank)
    print(
        format_fast_recommendation_audit(
            audit_fast_recommendations(
                state,
                rankings,
                path_bank,
                steps=args.steps,
                budget_ms=args.budget_ms,
            )
        )
    )


@dataclass(frozen=True)
class FastRecommendationAuditRow:
    pick: int
    player_name: str
    score: float
    elapsed_ms: float
    sample_quality: str
    similar_paths: int
    passed: bool


def audit_fast_recommendations(
    state: DraftState,
    rankings: list[RankingRow],
    path_bank: DraftPathBank,
    *,
    steps: int,
    budget_ms: float,
) -> list[FastRecommendationAuditRow]:
    rows: list[FastRecommendationAuditRow] = []
    for _step in range(steps):
        if state.is_complete:
            break
        start = perf_counter()
        context = build_path_bank_context(state, rankings, path_bank)
        recommendation = recommend_players(state, rankings, path_context=context)
        elapsed_ms = (perf_counter() - start) * 1000
        player = state.players[recommendation.primary.player_id]
        rows.append(
            FastRecommendationAuditRow(
                pick=state.current_overall_pick,
                player_name=player.full_name,
                score=recommendation.primary.total_score,
                elapsed_ms=elapsed_ms,
                sample_quality=context.sample_quality,
                similar_paths=context.similar_path_count,
                passed=elapsed_ms <= budget_ms,
            )
        )
        state = state.record_pick(recommendation.primary.player_id)
    return rows


def format_fast_recommendation_audit(rows: list[FastRecommendationAuditRow]) -> str:
    passed_count = sum(row.passed for row in rows)
    lines = [f"Fast recommendation audit: {passed_count}/{len(rows)} within budget", ""]
    for row in rows:
        status = "PASS" if row.passed else "SLOW"
        lines.append(
            f"{status} pick={row.pick:<3} {row.elapsed_ms:>7.2f}ms "
            f"score={row.score:>7.1f} sample={row.sample_quality:<8} "
            f"paths={row.similar_paths:<5} {row.player_name}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    main()

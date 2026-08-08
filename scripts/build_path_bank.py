from argparse import ArgumentParser
from time import perf_counter

from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import build_path_bank
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


def main() -> None:
    parser = ArgumentParser(description="Build a pre-draft BayesianDraft path bank.")
    add_snapshot_argument(parser)
    parser.add_argument("--out", required=True)
    parser.add_argument("--simulations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=1001)
    parser.add_argument("--candidate-limit", type=int, default=250)
    parser.add_argument(
        "--progress-every",
        type=int,
        default=25,
        help="Print progress after this many completed simulated paths.",
    )
    args = parser.parse_args()

    snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    start = perf_counter()
    print(
        f"Building path bank: 0/{args.simulations} paths "
        f"for snapshot {snapshot.snapshot.snapshot_id}"
    )
    path_bank = build_path_bank(
        state,
        build_baseline_rankings(snapshot),
        snapshot_id=snapshot.snapshot.snapshot_id,
        simulation_count=args.simulations,
        seed=args.seed,
        candidate_limit=args.candidate_limit,
        progress_callback=_progress_printer(
            progress_every=max(args.progress_every, 1),
            start=start,
        ),
    )
    path_bank.save(args.out)
    elapsed = perf_counter() - start
    print(
        f"Built path bank with {path_bank.metadata.simulation_count} paths "
        f"for snapshot {path_bank.metadata.snapshot_id} -> {args.out} "
        f"in {elapsed:.1f}s"
    )


def _progress_printer(progress_every: int, start: float):
    def print_progress(completed: int, total: int, seed: int, status: str) -> None:
        if status != "indexing" and completed < total and completed % progress_every != 0:
            return
        elapsed = perf_counter() - start
        rate = completed / elapsed if elapsed > 0 else 0
        remaining = max(total - completed, 0)
        eta = remaining / rate if rate > 0 else 0
        if status == "indexing":
            print(
                f"Building lookup tables after {completed}/{total} paths "
                f"(elapsed {elapsed:.1f}s)"
            )
            return
        print(
            f"Progress: {completed}/{total} paths "
            f"seed={seed} status={status} elapsed={elapsed:.1f}s eta={eta:.1f}s"
        )

    return print_progress


if __name__ == "__main__":
    main()

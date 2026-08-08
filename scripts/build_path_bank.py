from argparse import ArgumentParser

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
    args = parser.parse_args()

    snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    path_bank = build_path_bank(
        state,
        build_baseline_rankings(snapshot),
        snapshot_id=snapshot.snapshot.snapshot_id,
        simulation_count=args.simulations,
        seed=args.seed,
        candidate_limit=args.candidate_limit,
    )
    path_bank.save(args.out)
    print(
        f"Built path bank with {path_bank.metadata.simulation_count} paths "
        f"for snapshot {path_bank.metadata.snapshot_id} -> {args.out}"
    )


if __name__ == "__main__":
    main()

from argparse import ArgumentParser

from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.simulation import benchmark_remaining_draft
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


def main() -> None:
    parser = ArgumentParser(description="Run a seeded draft simulation smoke benchmark.")
    add_snapshot_argument(parser)
    args = parser.parse_args()

    snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    result = benchmark_remaining_draft(state, build_baseline_rankings(snapshot))
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

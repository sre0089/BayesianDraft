from argparse import ArgumentParser

from bayesiandraft.draft import (
    apply_rehearsal_scenario,
    load_rehearsal_scenario,
    summarize_draft_state,
)
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


def main() -> None:
    parser = ArgumentParser(description="Print a BayesianDraft draft-state summary.")
    parser.add_argument("--scenario")
    add_snapshot_argument(parser)
    args = parser.parse_args()

    _snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    if args.scenario:
        state = apply_rehearsal_scenario(state, load_rehearsal_scenario(args.scenario))

    print(summarize_draft_state(state).model_dump_json(indent=2))


if __name__ == "__main__":
    main()

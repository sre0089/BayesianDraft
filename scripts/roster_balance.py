from argparse import ArgumentParser

from bayesiandraft.draft import (
    apply_rehearsal_scenario,
    build_roster_balance_report,
    load_rehearsal_scenario,
)
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


def main() -> None:
    parser = ArgumentParser(description="Print a roster balance report.")
    parser.add_argument("--manager-id", default="user_manager")
    parser.add_argument("--scenario", default="data/fixtures/rehearsal_user_pick_8.json")
    add_snapshot_argument(parser)
    args = parser.parse_args()

    _snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    state = apply_rehearsal_scenario(state, load_rehearsal_scenario(args.scenario))
    print(build_roster_balance_report(state, args.manager_id).model_dump_json(indent=2))


if __name__ == "__main__":
    main()

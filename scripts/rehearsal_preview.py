from argparse import ArgumentParser

from bayesiandraft.draft import (
    apply_rehearsal_scenario,
    load_rehearsal_scenario,
)
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


def main() -> None:
    parser = ArgumentParser(description="Preview a BayesianDraft rehearsal scenario.")
    parser.add_argument(
        "scenario",
        nargs="?",
        default="data/fixtures/rehearsal_user_pick_8.json",
    )
    add_snapshot_argument(parser)
    args = parser.parse_args()

    _snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    scenario = load_rehearsal_scenario(args.scenario)
    rehearsed = apply_rehearsal_scenario(state, scenario)
    print(
        f"{scenario.scenario_id}: current_pick={rehearsed.current_overall_pick} "
        f"manager_on_clock={rehearsed.manager_on_clock}"
    )


if __name__ == "__main__":
    main()

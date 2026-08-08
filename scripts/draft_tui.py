from argparse import ArgumentParser
from pathlib import Path

from bayesiandraft.cli import CliDraftConfig, CliDraftController, run_tui
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


def main() -> None:
    parser = ArgumentParser(description="Run the interactive BayesianDraft terminal UI.")
    add_snapshot_argument(parser)
    parser.add_argument("--scenario", help="Optional rehearsal scenario to load at startup.")
    parser.add_argument(
        "--auto-pick-to-user",
        action="store_true",
        help="Auto-draft highest-ranked players until the configured user manager is on clock.",
    )
    parser.add_argument(
        "--save-path",
        default="data/processed/cli_draft_state.json",
        help="Where the terminal UI saves draft state.",
    )
    parser.add_argument(
        "--no-autosave",
        action="store_true",
        help="Disable automatic saves after draft, undo, redo, and auto-pick actions.",
    )
    parser.add_argument(
        "--load-save",
        action="store_true",
        help="Resume the draft state from --save-path if the file exists.",
    )
    args = parser.parse_args()

    snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    controller = CliDraftController(
        snapshot=snapshot,
        state=state,
        config=CliDraftConfig(
            save_path=Path(args.save_path),
            scenario_path=None if args.scenario is None else Path(args.scenario),
            auto_pick_to_user=args.auto_pick_to_user,
            autosave=not args.no_autosave,
            load_existing_save=args.load_save,
        ),
    )
    run_tui(controller)


if __name__ == "__main__":
    main()

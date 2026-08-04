from argparse import ArgumentParser
from pathlib import Path

from bayesiandraft.draft import (
    apply_rehearsal_scenario,
    load_rehearsal_scenario,
)
from bayesiandraft.rankings import build_baseline_rankings
from bayesiandraft.recommendations import recommend_players
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


def main() -> None:
    parser = ArgumentParser(description="Export BayesianDraft baseline recommendations.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--scenario")
    add_snapshot_argument(parser)
    args = parser.parse_args()

    snapshot, state = load_snapshot_and_draft_state(args.snapshot)
    if args.scenario:
        state = apply_rehearsal_scenario(state, load_rehearsal_scenario(args.scenario))

    recommendations = recommend_players(state, build_baseline_rankings(snapshot))
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(recommendations.model_dump_json(indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

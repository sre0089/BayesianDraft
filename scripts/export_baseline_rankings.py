from argparse import ArgumentParser
from pathlib import Path

from bayesiandraft.rankings import (
    build_baseline_rankings,
    export_rankings_csv,
    export_rankings_json,
)
from scripts.common import add_snapshot_argument, load_snapshot_and_draft_state


def main() -> None:
    parser = ArgumentParser(description="Export baseline BayesianDraft rankings.")
    add_snapshot_argument(parser)
    parser.add_argument("--out", required=True, help="Output file path.")
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Export format.",
    )
    args = parser.parse_args()

    snapshot, _state = load_snapshot_and_draft_state(args.snapshot)
    rankings = build_baseline_rankings(snapshot)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "json":
        export_rankings_json(rankings, output_path)
    else:
        export_rankings_csv(rankings, output_path)


if __name__ == "__main__":
    main()

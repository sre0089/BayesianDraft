from argparse import ArgumentParser
from pathlib import Path

from bayesiandraft.data import load_player_snapshot
from bayesiandraft.rankings import (
    build_baseline_rankings,
    export_rankings_csv,
    export_rankings_json,
)


def main() -> None:
    parser = ArgumentParser(description="Export baseline BayesianDraft rankings.")
    parser.add_argument(
        "--snapshot",
        default="data/fixtures/baseline_players_2026.json",
        help="Path to a validated player snapshot JSON file.",
    )
    parser.add_argument("--out", required=True, help="Output file path.")
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Export format.",
    )
    args = parser.parse_args()

    rankings = build_baseline_rankings(load_player_snapshot(args.snapshot))
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "json":
        export_rankings_json(rankings, output_path)
    else:
        export_rankings_csv(rankings, output_path)


if __name__ == "__main__":
    main()

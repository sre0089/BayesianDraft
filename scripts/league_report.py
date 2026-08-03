from argparse import ArgumentParser

from bayesiandraft.config import load_league_config
from bayesiandraft.config.report import build_league_sanity_report


def main() -> None:
    parser = ArgumentParser(description="Print a BayesianDraft league sanity report.")
    parser.add_argument("--config", default="configs/leagues/espn_2026.yaml")
    args = parser.parse_args()

    report = build_league_sanity_report(load_league_config(args.config))
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

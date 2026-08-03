from argparse import ArgumentParser

from bayesiandraft.data import build_snapshot_health_report, load_player_snapshot


def main() -> None:
    parser = ArgumentParser(description="Print a BayesianDraft player snapshot health report.")
    parser.add_argument("--snapshot", default="data/fixtures/baseline_players_2026.json")
    args = parser.parse_args()

    report = build_snapshot_health_report(load_player_snapshot(args.snapshot))
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

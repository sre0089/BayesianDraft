from argparse import ArgumentParser

from bayesiandraft.hardening import run_preflight_checks


def main() -> None:
    parser = ArgumentParser(description="Run BayesianDraft draft-day preflight checks.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    report = run_preflight_checks()
    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        for check in report.checks:
            print(f"{check.status.value.upper()} {check.name}: {check.message}")

    raise SystemExit(1 if report.is_blocked else 0)


if __name__ == "__main__":
    main()

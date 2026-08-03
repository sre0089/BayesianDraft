from argparse import ArgumentParser

from bayesiandraft.data import default_refresh_plan, run_refresh_plan


def main() -> None:
    parser = ArgumentParser(description="Run BayesianDraft local data refresh hooks.")
    parser.add_argument("--json", action="store_true", help="Print JSON result payload.")
    args = parser.parse_args()

    results = run_refresh_plan(default_refresh_plan())
    if args.json:
        print("[" + ",".join(result.model_dump_json() for result in results) + "]")
    else:
        for result in results:
            status = "OK" if result.ok else "FAIL"
            print(f"{status} {result.dataset_name}: {result.message}")

    raise SystemExit(0 if all(result.ok for result in results) else 1)


if __name__ == "__main__":
    main()

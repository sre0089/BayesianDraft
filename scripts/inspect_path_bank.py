from argparse import ArgumentParser

from bayesiandraft.simulation import DraftPathBank


def main() -> None:
    parser = ArgumentParser(description="Inspect a BayesianDraft path-bank artifact.")
    parser.add_argument("path_bank")
    args = parser.parse_args()

    print(format_path_bank_report(DraftPathBank.load(args.path_bank)))


def format_path_bank_report(path_bank: DraftPathBank) -> str:
    metadata = path_bank.metadata
    lines = [
        "Draft path bank",
        f"schema: {metadata.schema_version}",
        f"snapshot: {metadata.snapshot_id}",
        f"league hash: {metadata.league_config_hash}",
        f"paths: {len(path_bank.paths)}",
        f"seed: {metadata.seed}",
        f"candidate limit: {metadata.candidate_limit}",
        "",
        "Lookup coverage",
        f"player availability picks: {len(path_bank.player_availability_by_pick)}",
        f"position value picks: {len(path_bank.position_value_by_pick)}",
        f"position dropoff picks: {len(path_bank.position_dropoff_by_pick)}",
    ]
    if path_bank.position_value_by_pick:
        first_pick = sorted(path_bank.position_value_by_pick, key=int)[0]
        values = path_bank.position_value_by_pick[first_pick]
        parts = " ".join(f"{position}:{value:.1f}" for position, value in values.items())
        lines.extend(["", f"Pick {first_pick} expected best VORP", parts])
    return "\n".join(lines)


if __name__ == "__main__":
    main()

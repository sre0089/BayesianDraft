import subprocess
from argparse import ArgumentParser
from dataclasses import dataclass


@dataclass(frozen=True)
class CiCommand:
    label: str
    command: list[str]
    cwd: str = "."


CI_COMMANDS = [
    CiCommand("python-tests", ["pytest", "-q"]),
    CiCommand("ruff", ["ruff", "check", "."]),
    CiCommand(
        "mypy",
        [
            "mypy",
            "bayesiandraft",
            "apps/api/src",
            "scripts/export_baseline_rankings.py",
            "scripts/verify_ingestion_manifest.py",
            "scripts/preflight.py",
            "scripts/data_refresh.py",
            "scripts/export_openapi.py",
            "scripts/version_info.py",
            "scripts/rehearsal_preview.py",
            "scripts/validate_local.py",
            "scripts/league_report.py",
            "scripts/snapshot_health.py",
            "scripts/export_recommendations.py",
            "scripts/draft_summary.py",
            "scripts/roster_balance.py",
            "scripts/sim_benchmark.py",
            "scripts/privacy_scan.py",
            "scripts/check_docs_index.py",
            "scripts/ci_local.py",
            "scripts/import_snapshot.py",
            "scripts/common.py",
            "scripts/draft_tui.py",
        ],
    ),
    CiCommand("web-tests", ["npm", "test"], cwd="apps/web"),
    CiCommand("web-lint", ["npm", "run", "lint"], cwd="apps/web"),
    CiCommand("web-build", ["npm", "run", "build"], cwd="apps/web"),
]


def command_labels() -> list[str]:
    return [command.label for command in CI_COMMANDS]


def main() -> None:
    parser = ArgumentParser(description="Run local BayesianDraft CI checks.")
    parser.add_argument("--list", action="store_true", help="List checks without running them.")
    args = parser.parse_args()

    if args.list:
        for label in command_labels():
            print(label)
        return

    for command in CI_COMMANDS:
        print(f"== {command.label}")
        result = subprocess.run(command.command, cwd=command.cwd, check=False)
        if result.returncode != 0:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

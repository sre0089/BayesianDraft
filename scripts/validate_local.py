import subprocess
import sys

COMMANDS = [
    [sys.executable, "scripts/preflight.py"],
    [sys.executable, "scripts/data_refresh.py"],
    [sys.executable, "scripts/rehearsal_preview.py"],
    [sys.executable, "scripts/version_info.py"],
]


def main() -> None:
    for command in COMMANDS:
        result = subprocess.run(command, check=False, text=True)
        if result.returncode != 0:
            raise SystemExit(result.returncode)
    print("local validation ok")


if __name__ == "__main__":
    main()

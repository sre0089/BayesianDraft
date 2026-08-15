import re
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "data/processed",
    "data/raw",
    "data/snapshots",
    "dist",
    "node_modules",
}

DENYLIST = [
    "Man" + "esh",
    "Jus" + "tin",
    "Dav" + "id",
    "Ar" + "jun",
    "An" + "i",
    "No" + "lan",
    "Shre" + "yes",
    "Kr" + "ish",
    "Matt" + "hew",
    "Sur" + "ya",
    "Nay" + "an",
    "Aad" + "arsh",
    "Ar" + "yan",
    "Sar" + "thak",
]


def scan_repo(root: str | Path = ".") -> list[str]:
    root_path = Path(root)
    findings = []
    patterns = [re.compile(rf"\b{re.escape(item)}\b", re.IGNORECASE) for item in DENYLIST]
    for path in sorted(root_path.rglob("*")):
        if not path.is_file() or _skipped(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in patterns):
                findings.append(f"{path}:{line_number}")
    return findings


def _skipped(path: Path) -> bool:
    path_text = path.as_posix()
    if path.name.endswith(".local.yaml"):
        return True
    return any(
        part in path.parts or f"/{part}/" in path_text or path_text.startswith(f"{part}/")
        for part in SKIP_DIRS
    )


def main() -> None:
    findings = scan_repo()
    for finding in findings:
        print(finding)
    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()

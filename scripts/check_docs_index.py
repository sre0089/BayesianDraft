import re
from pathlib import Path

LINK_PATTERN = re.compile(r"\]\(([^)]+\.md)\)")


def missing_index_links(index_path: str | Path = "docs/README.md") -> list[str]:
    path = Path(index_path)
    text = path.read_text(encoding="utf-8")
    return [
        link
        for link in LINK_PATTERN.findall(text)
        if not (path.parent / link).exists()
    ]


def main() -> None:
    missing = missing_index_links()
    for link in missing:
        print(link)
    raise SystemExit(1 if missing else 0)


if __name__ == "__main__":
    main()

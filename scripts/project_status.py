import re
from pathlib import Path

from pydantic import BaseModel

from bayesiandraft.release import build_info_from_env

COMPLETE_PATTERN = re.compile(r"^- Milestone (?P<number>\d+): complete$", re.MULTILINE)


class ProjectStatusReport(BaseModel):
    project: str
    version: str
    completed_milestones: int
    latest_completed_milestone: int | None


def build_project_status_report(
    milestone_path: str | Path = "docs/milestones.md",
) -> ProjectStatusReport:
    text = Path(milestone_path).read_text(encoding="utf-8")
    completed = [int(match.group("number")) for match in COMPLETE_PATTERN.finditer(text)]
    build_info = build_info_from_env()
    return ProjectStatusReport(
        project=build_info.name,
        version=build_info.version,
        completed_milestones=len(completed),
        latest_completed_milestone=max(completed) if completed else None,
    )


def main() -> None:
    print(build_project_status_report().model_dump_json(indent=2))


if __name__ == "__main__":
    main()

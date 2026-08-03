from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from bayesiandraft.data.ingestion import (
    IngestionManifestError,
    load_ingestion_manifest,
    verify_ingestion_manifest,
)


class RefreshMode(StrEnum):
    LOCAL_VERIFY = "local_verify"
    DRY_RUN = "dry_run"


class DataRefreshStep(BaseModel):
    dataset_name: str
    mode: RefreshMode
    manifest_path: str


class DataRefreshResult(BaseModel):
    dataset_name: str
    mode: RefreshMode
    ok: bool
    message: str


class DataRefreshPlan(BaseModel):
    steps: list[DataRefreshStep] = Field(default_factory=list)


def default_refresh_plan() -> DataRefreshPlan:
    return DataRefreshPlan(
        steps=[
            DataRefreshStep(
                dataset_name="baseline_players",
                mode=RefreshMode.LOCAL_VERIFY,
                manifest_path="data/manifests/baseline_players_2026.json",
            )
        ]
    )


def run_refresh_plan(plan: DataRefreshPlan, *, root: str | Path = ".") -> list[DataRefreshResult]:
    return [_run_refresh_step(step, root=root) for step in plan.steps]


def _run_refresh_step(step: DataRefreshStep, *, root: str | Path) -> DataRefreshResult:
    if step.mode == RefreshMode.DRY_RUN:
        return DataRefreshResult(
            dataset_name=step.dataset_name,
            mode=step.mode,
            ok=True,
            message="Dry run only; no external data fetched.",
        )

    try:
        manifest = load_ingestion_manifest(Path(root) / step.manifest_path)
        verify_ingestion_manifest(manifest, root=root)
    except IngestionManifestError as exc:
        return DataRefreshResult(
            dataset_name=step.dataset_name,
            mode=step.mode,
            ok=False,
            message=str(exc),
        )
    return DataRefreshResult(
        dataset_name=step.dataset_name,
        mode=step.mode,
        ok=True,
        message="Local manifest verified.",
    )

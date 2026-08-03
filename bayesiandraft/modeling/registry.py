import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class ModelRegistryEntry(BaseModel):
    model_name: str
    model_version: str
    training_code_version: str
    data_snapshot_ids: list[str]
    feature_schema_version: str
    trained_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    validation_metrics: dict[str, float] = Field(default_factory=dict)
    calibration_metrics: dict[str, float] = Field(default_factory=dict)
    runtime_dependencies: list[str] = Field(default_factory=list)
    known_limitations: list[str] = Field(default_factory=list)
    active: bool = False


class ModelRegistry(BaseModel):
    entries: list[ModelRegistryEntry] = Field(default_factory=list)


def load_model_registry(path: str | Path) -> ModelRegistry:
    registry_path = Path(path)
    if not registry_path.exists():
        return ModelRegistry()
    raw_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    return ModelRegistry.model_validate(raw_registry)


def write_model_registry(path: str | Path, registry: ModelRegistry) -> None:
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        registry.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def active_model(registry: ModelRegistry, model_name: str) -> ModelRegistryEntry | None:
    active_entries = [
        entry
        for entry in registry.entries
        if entry.model_name == model_name and entry.active
    ]
    if not active_entries:
        return None
    active_entries.sort(key=lambda entry: entry.trained_at, reverse=True)
    return active_entries[0]

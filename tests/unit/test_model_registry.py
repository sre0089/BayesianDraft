from datetime import UTC, datetime

from bayesiandraft.modeling import (
    ModelRegistry,
    ModelRegistryEntry,
    active_model,
    load_model_registry,
    write_model_registry,
)


def test_missing_registry_loads_empty() -> None:
    assert load_model_registry("missing.json") == ModelRegistry()


def test_writes_and_loads_model_registry(tmp_path) -> None:
    registry_path = tmp_path / "registry.json"
    registry = ModelRegistry(
        entries=[
            ModelRegistryEntry(
                model_name="projection",
                model_version="baseline_v1",
                training_code_version="manual",
                data_snapshot_ids=["synthetic_players_2026_v1"],
                feature_schema_version="1",
                trained_at=datetime(2026, 8, 3, tzinfo=UTC),
                active=True,
            )
        ]
    )

    write_model_registry(registry_path, registry)

    assert load_model_registry(registry_path) == registry


def test_active_model_returns_latest_active_entry() -> None:
    old = ModelRegistryEntry(
        model_name="projection",
        model_version="old",
        training_code_version="manual",
        data_snapshot_ids=["snapshot"],
        feature_schema_version="1",
        trained_at=datetime(2026, 8, 1, tzinfo=UTC),
        active=True,
    )
    new = old.model_copy(
        update={
            "model_version": "new",
            "trained_at": datetime(2026, 8, 3, tzinfo=UTC),
        }
    )

    assert active_model(ModelRegistry(entries=[old, new]), "projection") == new

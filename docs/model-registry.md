# Model Registry

Model artifacts must be versioned and traceable to data snapshots.

Each artifact should record:

- Model name and version
- Training code version
- Data snapshot IDs
- Feature schema version
- Training timestamp
- Validation metrics
- Calibration metrics where relevant
- Runtime dependencies
- Known limitations

MLflow may be introduced only if the added operational complexity is justified.

## Current Implementation

Milestone 22 adds `bayesiandraft.modeling`.

Current helpers:

- `ModelRegistryEntry`
- `ModelRegistry`
- `load_model_registry`
- `write_model_registry`
- `active_model`

The current registry is local JSON metadata only. Model binaries and external registry services are intentionally deferred.

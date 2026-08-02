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

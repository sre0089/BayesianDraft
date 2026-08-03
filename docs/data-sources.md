# Data Sources

BayesianDraft requires reproducible data governance.

## Source Categories

- NFL performance data: nflverse and other permitted public sources.
- Market data: ESPN rankings/ADP, Underdog ADP, and other permitted sources.
- Context data: injuries, practice reports, depth charts, transactions, suspensions, coaching changes, team projections.

## Governance

Every dataset must include:

- Source name and URL
- Retrieval timestamp
- Season
- Snapshot ID
- File checksum
- Schema version
- Preprocessing version
- License or usage notes
- Raw immutable copy
- Processed derived copy
- Known limitations

Do not silently scrape or commit unlicensed proprietary data.

## Ingestion Manifests

`bayesiandraft.data.ingestion` handles reproducible manifest records.

Current helpers:

- `IngestionManifestEntry` validates required provenance fields.
- `sha256_file` calculates file checksums.
- `load_ingestion_manifest` and `write_ingestion_manifest` handle JSON manifests.
- `verify_ingestion_manifest` confirms processed files exist and match recorded checksums.

The CLI verifier is:

```bash
PYTHONPATH=. python scripts/verify_ingestion_manifest.py data/manifests/baseline_players_2026.json
```

Use the project environment's Python interpreter when local system Python does not include project dependencies.

## Data Refresh Hooks

Local refresh hooks are available:

```bash
PYTHONPATH=. python scripts/data_refresh.py
PYTHONPATH=. python scripts/data_refresh.py --json
```

Current refresh behavior verifies local manifests and does not fetch external data.

## Snapshot Health

Snapshot health reporting is available:

```bash
PYTHONPATH=. python scripts/snapshot_health.py
```

This reports player count, projection coverage, ADP coverage, injury record count, and fixture warnings.

## Current Baseline Fixture

The current baseline fixture is `data/fixtures/baseline_players_2026.json`.

This file is synthetic public fixture data. It exists to exercise schemas, loaders, ranking logic, and UI/API workflows before real data ingestion is implemented. It must not be presented as real projections, real ADP, or real player analysis.

The companion manifest is `data/manifests/baseline_players_2026.json`.
It now follows the ingestion manifest schema and records a SHA-256 checksum for the processed fixture.

The fixture includes:

- player records
- season projection records
- ADP records
- snapshot provenance

Injury records are intentionally empty until an injury source and schema policy are implemented.

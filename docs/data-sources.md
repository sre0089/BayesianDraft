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

## Current Baseline Fixture

Milestone 4 adds `data/fixtures/baseline_players_2026.json`.

This file is synthetic public fixture data. It exists to exercise schemas, loaders, ranking logic, and UI/API workflows before real data ingestion is implemented. It must not be presented as real projections, real ADP, or real player analysis.

The companion manifest is `data/manifests/baseline_players_2026.json`.

The fixture includes:

- player records
- season projection records
- ADP records
- snapshot provenance

Injury records are intentionally empty until an injury source and schema policy are implemented.

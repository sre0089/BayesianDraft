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

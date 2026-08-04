# Local Data Import

BayesianDraft can import user-provided projection data into the same `PlayerSnapshot` JSON shape used by the ranking, recommendation, simulation, and API layers.

The importer is local-first. It reads files from your machine, writes processed JSON snapshots, and can write a manifest with checksum metadata. Do not commit proprietary projections, private league exports, credentials, cookies, or raw downloaded datasets.

## Snapshot CSV Contract

Use one CSV row per player. The importer accepts player metadata, season projection values, and optional ADP fields in a single file.

Required columns:

| Column | Description |
| --- | --- |
| `player_id` | Stable ID for the player within this snapshot |
| `full_name` | Display name |
| `position` | One of `QB`, `RB`, `WR`, `TE`, `K`, `DST` |
| `projected_points` | Mean season fantasy points |

Optional player columns:

| Column | Description |
| --- | --- |
| `team` | NFL team abbreviation or defense team ID |
| `bye_week` | NFL bye week, 1 through 18 |
| `status` | Player status, defaults to `active` |
| `first_name` | First name |
| `last_name` | Last name |

Optional projection columns:

| Column | Description |
| --- | --- |
| `median_points` | Median season fantasy points, defaults to `projected_points` |
| `floor_points` | Lower projection quantile, defaults to 80% of `projected_points` |
| `ceiling_points` | Upper projection quantile, defaults to 120% of `projected_points` |
| `games_played` | Expected games played |

Optional ADP columns:

| Column | Description |
| --- | --- |
| `overall_adp` | Overall average draft position |
| `position_adp` | Positional ADP |
| `adp_rank` | Overall market rank |

## Example

```csv
player_id,full_name,position,team,projected_points,median_points,floor_points,ceiling_points,games_played,overall_adp,position_adp,adp_rank,bye_week
rb_001,Example RB One,RB,CCC,285,280,220,340,16.5,5,1,5,8
wr_001,Example WR One,WR,FFF,270,268,210,325,16.0,8,1,8,9
qb_001,Example QB One,QB,AAA,330,326,270,390,16.5,32,1,32,6
```

## Import Command

```bash
PYTHONPATH=. python scripts/import_snapshot.py \
  --players path/to/projections.csv \
  --out data/processed/my_snapshot.json \
  --manifest-out data/manifests/my_snapshot.json \
  --snapshot-id my_snapshot_2026_v1 \
  --season 2026 \
  --source "user-provided" \
  --license-notes "Local user-provided projection file; do not redistribute."
```

The JSON snapshot can be loaded with `bayesiandraft.data.load_player_snapshot`.

The manifest records:

- snapshot ID
- source name and optional source URL
- retrieval timestamp
- processed snapshot path
- optional raw CSV path
- checksum
- schema version
- preprocessing version
- row count
- license notes

## Validation Rules

- Player IDs must be unique.
- Required columns must exist and contain values.
- Positions must match the supported position enum.
- Numeric projection and ADP fields must parse as numbers.
- `floor_points` must be less than or equal to `ceiling_points`.
- `bye_week`, when present, must be between 1 and 18.
- ADP records are only emitted for rows with `overall_adp`.

## Privacy And Licensing

The importer does not validate whether a source may be redistributed. That responsibility stays with the user. Keep third-party projections, private league exports, and downloaded raw files out of commits unless their license clearly allows redistribution.

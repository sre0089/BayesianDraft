# Local Data Import

BayesianDraft can import user-provided projection data into the same `PlayerSnapshot` JSON shape used by the ranking, recommendation, simulation, and API layers.

The importer is local-first. It reads files from your machine, writes processed JSON snapshots, and can write a manifest with checksum metadata. Do not commit proprietary projections, private league exports, credentials, cookies, or raw downloaded datasets.

## Point Projection CSV Contract

Use this contract when your source already provides fantasy point totals. The importer accepts one CSV row per player with player metadata, season projection values, and optional ADP fields in a single file.

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

## Point Projection Example

```csv
player_id,full_name,position,team,projected_points,median_points,floor_points,ceiling_points,games_played,overall_adp,position_adp,adp_rank,bye_week
rb_001,Example RB One,RB,CCC,285,280,220,340,16.5,5,1,5,8
wr_001,Example WR One,WR,FFF,270,268,210,325,16.0,8,1,8,9
qb_001,Example QB One,QB,AAA,330,326,270,390,16.5,32,1,32,6
```

## Stat Projection CSV Contract

Use this contract when your source provides football stat projections instead of fantasy point totals. The importer computes `projected_points` from the configured league scoring rules, then writes the same `PlayerSnapshot` JSON used everywhere else in the project.

Required columns:

| Column | Description |
| --- | --- |
| `player_id` | Stable ID for the player within this snapshot |
| `full_name` | Display name |
| `position` | One of `QB`, `RB`, `WR`, `TE`, `K`, `DST` |

Optional player and ADP columns are the same as the point projection contract. Any missing stat column is treated as zero.

Supported offensive stat columns:

| Column | Description |
| --- | --- |
| `passing_yards` | Passing yards |
| `passing_touchdowns` | Passing touchdowns |
| `interceptions_thrown` | Interceptions thrown |
| `passing_two_point_conversions` | Passing two-point conversions |
| `rushing_yards` | Rushing yards |
| `rushing_touchdowns` | Rushing touchdowns |
| `rushing_two_point_conversions` | Rushing two-point conversions |
| `receiving_yards` | Receiving yards |
| `receptions` | Receptions |
| `receiving_touchdowns` | Receiving touchdowns |
| `receiving_two_point_conversions` | Receiving two-point conversions |

Supported kicker stat columns:

| Column | Description |
| --- | --- |
| `pat_made` | Made extra points |
| `field_goal_missed` | Missed field goals |
| `fg_made_0_39` | Made field goals from 0 to 39 yards |
| `fg_made_40_49` | Made field goals from 40 to 49 yards |
| `fg_made_50_59` | Made field goals from 50 to 59 yards |
| `fg_made_60_plus` | Made field goals from 60 or more yards |

Supported defense/special teams stat columns:

| Column | Description |
| --- | --- |
| `dst_touchdowns` | Defense/special teams touchdowns |
| `dst_sacks` | Sacks |
| `dst_interceptions` | Defensive interceptions |
| `dst_fumble_recoveries` | Fumble recoveries |
| `dst_safeties` | Safeties |
| `dst_blocked_kicks` | Blocked kicks |

## Stat Projection Example

```csv
player_id,full_name,position,team,passing_yards,passing_touchdowns,interceptions_thrown,rushing_yards,rushing_touchdowns,overall_adp,bye_week
qb_001,Example QB One,QB,AAA,4000,30,10,250,3,42,6
```

## Import Commands

Point projection CSV:

```bash
PYTHONPATH=. python scripts/import_snapshot.py \
  --mode points \
  --players path/to/projections.csv \
  --out data/processed/my_snapshot.json \
  --manifest-out data/manifests/my_snapshot.json \
  --snapshot-id my_snapshot_2026_v1 \
  --season 2026 \
  --source "user-provided" \
  --license-notes "Local user-provided projection file; do not redistribute."
```

Stat projection CSV:

```bash
PYTHONPATH=. python scripts/import_snapshot.py \
  --mode stats \
  --league-config configs/leagues/espn_2026.yaml \
  --players path/to/stat_projections.csv \
  --out data/processed/my_stat_snapshot.json \
  --manifest-out data/manifests/my_stat_snapshot.json \
  --snapshot-id my_stat_snapshot_2026_v1 \
  --season 2026 \
  --source "user-provided" \
  --license-notes "Local user-provided stat projection file; do not redistribute."
```

The JSON snapshot can be loaded with `bayesiandraft.data.load_player_snapshot`.

## Public Rankings Pull

BayesianDraft can pull the latest public DynastyProcess/FantasyPros expert consensus rankings:

```bash
PYTHONPATH=. python scripts/pull_dynastyprocess.py
```

This writes:

- raw CSV: `data/raw/dynastyprocess_db_fpecr_latest.csv`
- processed snapshot: `data/processed/dynastyprocess_rankings_2026.json`
- local manifest: `data/processed/dynastyprocess_rankings_2026.manifest.json`

Then run the terminal draft room with:

```bash
PYTHONPATH=. python scripts/draft_tui.py \
  --snapshot data/processed/dynastyprocess_rankings_2026.json \
  --auto-pick-to-user
```

Source notes:

- Data source: DynastyProcess open data repository.
- Ranking source: FantasyPros expert consensus rankings as distributed by DynastyProcess.
- Projection fields in this snapshot are rank-derived proxies so the current engine can run. They are not independent statistical projections.

## Using Imported Snapshots

Most local commands accept `--snapshot`:

```bash
PYTHONPATH=. python scripts/export_baseline_rankings.py \
  --snapshot data/processed/my_snapshot.json \
  --out /tmp/rankings.json

PYTHONPATH=. python scripts/export_recommendations.py \
  --snapshot data/processed/my_snapshot.json \
  --out /tmp/recommendations.json

PYTHONPATH=. python scripts/sim_benchmark.py \
  --snapshot data/processed/my_snapshot.json
```

The local API can use an imported snapshot through an environment variable:

```bash
BAYESIANDRAFT_PLAYER_SNAPSHOT_PATH=data/processed/my_snapshot.json \
  uvicorn bayesiandraft_api.main:app --app-dir apps/api/src --reload
```

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
- Stat projection rows must score to a non-zero fantasy-point total.
- `floor_points` must be less than or equal to `ceiling_points`.
- `bye_week`, when present, must be between 1 and 18.
- ADP records are only emitted for rows with `overall_adp`.

## Privacy And Licensing

The importer does not validate whether a source may be redistributed. That responsibility stays with the user. Keep third-party projections, private league exports, and downloaded raw files out of commits unless their license clearly allows redistribution.

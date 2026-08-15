# Data Schema

This document describes the stable internal records BayesianDraft uses for players, projections, draft state, recommendations, and simulation outputs.

Most implemented Pydantic records live in `bayesiandraft.domain`.

## Common Rules

- Records use stable string identifiers instead of provider-specific IDs as primary keys.
- Provider IDs belong in mapping fields such as `source_player_ids`.
- Source provenance must point to a snapshot ID or source metadata record.
- Probability fields are bounded between 0 and 1.
- Projection intervals must be ordered: lower quantile cannot exceed upper quantile.
- Weekly projections require a week value.

## PlayerRecord

Purpose: canonical player identity and context.

Primary key: `player_id`.

Required fields: `player_id`, `full_name`, `position`.

Optional fields include team, status, age, size, experience, rookie flag, draft metadata, bye week, source IDs, and validity dates.

Validation:

- `position` must be one of `QB`, `RB`, `WR`, `TE`, `K`, `DST`.
- `bye_week` must be between 1 and 18 when present.

## TeamRecord

Purpose: NFL team identity and season context.

Primary key: `team_id`.

Required fields: `team_id`, `abbreviation`, `full_name`, `season`.

Optional fields include conference, division, coach, stadium, offensive context, and defensive context.

## GameRecord

Purpose: scheduled or completed NFL game.

Primary key: `game_id`.

Required fields: `game_id`, `season`, `week`, `game_type`, `date`, `home_team_id`, `away_team_id`, `source`.

## WeeklyStatsRecord

Purpose: normalized weekly player stat line.

Foreign keys: `player_id`, `game_id`, `source_snapshot_id`.

The initial schema covers core passing, rushing, receiving, and fantasy-point fields. Extra fields are rejected until they are explicitly modeled.

## SeasonStatsRecord

Purpose: aggregate player season output.

Foreign key: `player_id`.

Extra fields are allowed for later position-specific stats while the core schema stabilizes.

## ProjectionRecord

Purpose: model or baseline player projection.

Primary key: `projection_id`.

Foreign keys: `player_id`, `data_snapshot_id`.

Required fields: projection ID, player ID, season, mean, median, lower quantile, upper quantile, model version, data snapshot ID, generated timestamp.

Validation:

- Weekly projections require `week`.
- `upper_quantile` must be greater than or equal to `lower_quantile`.

## ADPRecord

Purpose: market cost and rank data.

Primary key: `adp_id`.

Foreign keys: `player_id`, `snapshot_id`.

Required fields: ADP ID, player ID, source, format, scoring, date, overall ADP, snapshot ID.

## InjuryRecord

Purpose: injury status and uncertainty.

Primary key: `injury_id`.

Foreign key: `player_id`.

Validation: `confidence` must be between 0 and 1.

## DraftPickRecord

Purpose: auditable pick record.

Required fields: draft ID, overall pick, round, round pick, manager ID, player ID.

## RosterRecord

Purpose: roster state for a manager.

Primary key: `manager_id` within a draft.

Includes player IDs, starters, bench, IR, positional counts, vacancies, and strength summary.

## DraftStateRecord

Purpose: serialized draft state snapshot.

Primary key: `draft_id`.

Includes current pick, round, manager on clock, completed picks, available players, rosters, future user picks, undo/redo stacks, model version, data snapshot ID, simulation seed, and update timestamp.

## RecommendationRecord

Purpose: auditable model recommendation.

Primary key: `recommendation_id`.

Foreign keys: draft state ID, candidate player ID.

Validation: playoff probability, championship probability, next-pick availability, and confidence are bounded from 0 to 1.

## SimulationResultRecord

Purpose: candidate rollout or simulation summary.

Primary key: `simulation_id`.

Includes simulation count, seed, expected roster value, playoff probability, championship probability, downside metric, runtime, model versions, and snapshot ID.

## DataSnapshotRecord

Purpose: provenance record for a dataset snapshot.

Primary key: `snapshot_id`.

Required fields: dataset name, source, retrieval timestamp, season, checksum, processed path, schema version, preprocessing version, license notes, and row count.

## Known Limitations

- The first schema pass is intentionally compact and will expand as ingestion, projections, injuries, and simulations mature.
- Provider-specific raw fields should remain in raw/processed data layers until promoted into stable records.
- League configuration is currently modeled separately in `bayesiandraft.config`.

## Ranking Records

Baseline ranking outputs are currently represented by `RankingRow` in `bayesiandraft.rankings`. They are derived records rather than source snapshot records and include projected points, floor, median, ceiling, position rank, overall rank, tier, VORP, value above starter, ADP delta, sleeper score, and fade score.

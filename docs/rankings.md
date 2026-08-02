# Rankings

Milestone 5 implements transparent baseline rankings in `bayesiandraft.rankings`.

## Inputs

The baseline engine consumes a validated `PlayerSnapshot` containing:

- players
- projections
- ADP records

The current fixture is synthetic and lives at `data/fixtures/baseline_players_2026.json`.

## Formulas

Rows are first ranked within position by projected mean points.

Replacement points are configurable by replacement rank. Defaults:

- QB: 18
- RB: 42
- WR: 42
- TE: 18
- DST: 12
- K: 12

Starter threshold points are configurable by starter count. Defaults:

- QB: 12
- RB: 30
- WR: 30
- TE: 12
- DST: 12
- K: 12

Value metrics:

```text
VORP = projected_points - replacement_points
ValueAboveStarter = projected_points - starter_threshold_points
ADPDelta = overall_adp - overall_rank
SleeperScore = max(ADPDelta, 0) / adp_value_scale
FadeScore = max(-ADPDelta, 0) / adp_value_scale
```

Overall rank is sorted by:

1. VORP descending
2. projected points descending
3. player name ascending

## Tiers

Tiers are assigned within each position. A new tier starts when the gap from the previous player is greater than or equal to `tier_gap_points`.

## Exports

Use:

```bash
PYTHONPATH=. python scripts/export_baseline_rankings.py --out /tmp/rankings.json --format json
PYTHONPATH=. python scripts/export_baseline_rankings.py --out /tmp/rankings.csv --format csv
```

## Current Limitations

- The fixture data is synthetic.
- Replacement assumptions are simple defaults and will need league-calibrated tuning.
- No roster-aware live rank exists yet.
- No availability model is included yet.
- Sleeper/fade scores are transparent heuristics, not calibrated probabilities.

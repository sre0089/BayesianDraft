# Scoring

Scoring must be exact, pure, tested, and configuration-driven.

Initial league configuration should live at:

```text
configs/leagues/espn_2026.yaml
```

The scoring engine covers:

- Passing
- Rushing
- Receiving
- Kicking
- D/ST touchdowns and returns
- D/ST event scoring
- D/ST points-allowed buckets
- D/ST yards-allowed buckets

Boundary tests are required for every bucket and negative scoring rule.

## Implemented API

`bayesiandraft.scoring` provides pure Python scoring functions:

- `score_passing`
- `score_rushing`
- `score_receiving`
- `score_kicking`
- `score_defense_special_teams`
- `score_offense`

The functions accept immutable stat-line objects and a validated `LeagueConfig`.

## Covered Tests

- Passing yards, passing touchdowns, interceptions, and two-point conversions.
- Rushing yards, rushing touchdowns, and two-point conversions.
- Receiving yards, receptions, touchdowns, and two-point conversions.
- Combined offensive stat lines.
- Field-goal bucket boundaries.
- Missed-field-goal negative scoring.
- D/ST touchdown, return, and event scoring.
- D/ST points-allowed bucket boundaries.
- D/ST yards-allowed bucket boundaries.
- Negative bucket input rejection.

## Current Limitations

- Scoring functions operate on already-normalized stat-line objects.
- Raw provider stat ingestion is handled outside the scoring engine.
- Roster and lineup legality are not part of the scoring engine.

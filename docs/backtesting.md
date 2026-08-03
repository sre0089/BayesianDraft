# Backtesting

Backtesting must use time-based validation.

For a historical season, train only on information available before that season's draft. Use ADP, injuries, depth charts, and context as they existed at the time.

## Metrics

- Projection error: MAE, RMSE, pinball loss, calibration, interval coverage.
- Availability: Brier score, log loss, calibration, error by position/tier.
- Draft and roster: value gained versus ADP, starter points, bench utility, weekly points, playoff rate, championship rate, regret, runtime.

Compare against simple baselines before trusting complex models.

## Current Implementation

Milestone 19 adds `bayesiandraft.backtesting`.

Current helpers:

- `BacktestObservation`
- `mean_absolute_rank_error`
- `brier_score`
- `log_loss`
- `summarize_backtest`

Current limitations:

- Metrics operate on normalized observations.
- Historical data ingestion and time-split dataset assembly are still separate future work.

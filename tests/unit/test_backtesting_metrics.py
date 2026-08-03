from bayesiandraft.backtesting import (
    BacktestObservation,
    brier_score,
    log_loss,
    mean_absolute_rank_error,
    summarize_backtest,
)


def _observations() -> list[BacktestObservation]:
    return [
        BacktestObservation(
            observation_id="one",
            predicted_rank=1,
            actual_rank=3,
            predicted_probability=0.8,
            outcome=True,
        ),
        BacktestObservation(
            observation_id="two",
            predicted_rank=4,
            actual_rank=2,
            predicted_probability=0.25,
            outcome=False,
        ),
    ]


def test_rank_error_metric() -> None:
    assert mean_absolute_rank_error(_observations()) == 2


def test_probability_metrics() -> None:
    assert brier_score(_observations()) == 0.0512
    assert log_loss(_observations()) == 0.2554


def test_backtest_summary_handles_empty_input() -> None:
    summary = summarize_backtest([])

    assert summary.observation_count == 0
    assert summary.mean_absolute_rank_error == 0
    assert summary.brier_score == 0
    assert summary.log_loss == 0

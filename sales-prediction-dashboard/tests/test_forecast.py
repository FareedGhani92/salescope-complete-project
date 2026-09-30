import numpy as np
import pandas as pd
import pytest
from src.forecast import scores, feature_row, predict_recursive, fit_model, run_forecast, minimum_history
from src.data import make_daily


def test_zero_actuals_percentage_is_unavailable():
    assert scores([0, 0], [0, 1])["WAPE (%)"] is None
    assert scores([0, 0], [0, 1])["MAE"] == .5


def test_features_only_use_past_observations():
    history = np.arange(1, 29)
    row = feature_row(history, pd.Timestamp("2025-01-29"), 28)
    assert row[:4] == [28, 22, 15, 1]
    assert row[4] == np.mean(history[-7:])


def test_recursive_baseline_repeats_week_without_future_actuals():
    series = pd.Series(np.arange(28), index=pd.date_range("2025-01-01", periods=28))
    predictions = predict_recursive("Seasonal baseline", None, series, 14)
    np.testing.assert_equal(predictions, np.tile(np.arange(21, 28), 2))


def test_forecast_contract_and_temporal_boundaries(demo, demo_result):
    r = demo_result
    assert len(r.forecast) == 30
    assert r.forecast.date.min() == demo.date.max() + pd.Timedelta(days=1)
    assert r.model_name == r.comparison.iloc[0].Model
    assert r.test.date.max() == demo.date.max()
    assert r.test.date.min() > pd.Timestamp(r.metadata["training_start"])
    assert np.isfinite(r.forecast.predicted_sales).all()
    assert (r.forecast.lower_80 <= r.forecast.predicted_sales).all()
    assert (r.forecast.upper_80 >= r.forecast.predicted_sales).all()
    assert r.metrics["MAE"] == pytest.approx(np.abs(r.test.actual-r.test.predicted).mean())
    assert r.metadata["calibration_origins"] == 20


def test_holdout_does_not_change_model_selection(demo, demo_result):
    series = make_daily(demo)
    series.iloc[-30:] *= 20
    mutated = run_forecast(series, 30)
    pd.testing.assert_frame_equal(mutated.comparison, demo_result.comparison)
    np.testing.assert_allclose(mutated.test.predicted, demo_result.test.predicted)
    np.testing.assert_allclose(mutated.test.upper-mutated.test.predicted,
                               demo_result.test.upper-demo_result.test.predicted)


def test_constant_zero_series_is_valid():
    series = pd.Series(0., index=pd.date_range("2025-01-01", periods=minimum_history(7)))
    result = run_forecast(series, 7)
    assert result.model_name == "Seasonal baseline"
    assert result.metrics["MAE"] == 0
    assert result.metrics["WAPE (%)"] is None
    assert result.forecast.predicted_sales.eq(0).all()


@pytest.mark.parametrize("horizon", [7, 30, 90])
def test_short_history_is_rejected(horizon):
    series = pd.Series(1., index=pd.date_range("2025-01-01", periods=minimum_history(horizon)-1))
    with pytest.raises(ValueError, match="needs at least"):
        run_forecast(series, horizon)


def test_irregular_history_is_rejected():
    series = pd.Series(1., index=pd.date_range("2025-01-01", periods=200, freq="2D"))
    with pytest.raises(ValueError, match="complete, ordered"):
        run_forecast(series, 7)

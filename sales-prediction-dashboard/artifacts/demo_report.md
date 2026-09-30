# Salescope forecast report

- Scope: All sales
- Currency: USD
- Model: Ridge regression
- History: 2023-01-01 to 2025-12-31
- Forecast horizon: 30 days
- Forecast total: 1,320,180.01 USD
- Final test: 2025-12-02 to 2025-12-31
- Final test MAE: 4,055.79 USD
- Final test RMSE: 4,465.76 USD
- Final test WAPE (%): 9.063384489636224
- Seasonal baseline test MAE: 3,597.98
- Empirical range coverage on final test (%): 26.666666666666668
- Generated: 2026-09-30T13:59:38.224430+00:00

## Method and limitations

Models are selected by mean MAE over three earlier chronological forecast windows.
The selected model is evaluated on the final held-out period, then refitted on all
available history. Recursive forecasts never consume actual sales inside a forecast window.
Ranges use horizon-specific errors from 20 earlier, potentially overlapping origins.
They are empirical uncertainty estimates, not guaranteed probabilities. Individual
daily bounds must not be added together as a confidence interval for the total.
Sales may be negative when modeling net revenue with returns. Forecasts do not
model future promotions, prices, stockouts, or external shocks explicitly.
Synthetic demo results do not establish real-world accuracy.

## Reproduction metadata

```json
{
  "model": "Ridge regression",
  "currency": "USD",
  "scope": "All sales",
  "dataset_id": "919b5dad5765a777f7cc",
  "horizon_days": 30,
  "history_days": 1096,
  "training_start": "2023-01-01",
  "training_cutoff": "2025-12-31",
  "test_start": "2025-12-02",
  "test_end": "2025-12-31",
  "validation_folds": 3,
  "validation_horizon_days": 30,
  "selection_metric": "Validation MAE",
  "calibration_origins": 20,
  "interval_method": "80th percentile of absolute errors at each horizon; 20 overlapping historical origins; empirical, not guaranteed",
  "generated_at": "2026-09-30T13:59:38.224430+00:00",
  "random_seed": 2026,
  "python_version": "3.13.15",
  "model_implementation": "NumPy native v1",
  "features": [
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "mean_7",
    "mean_28",
    "std_7",
    "weekday_sin",
    "weekday_cos",
    "year_sin",
    "year_cos",
    "trend"
  ],
  "parameters": {
    "ridge_alpha": 10,
    "boosting_estimators": 40,
    "boosting_max_depth": 2,
    "boosting_max_splits": 16,
    "boosting_learning_rate": 0.075,
    "boosting_min_leaf": 12,
    "boosting_l2": 10
  },
  "data_source": "Synthetic retail demo",
  "execution_seconds": 0.59
}
```

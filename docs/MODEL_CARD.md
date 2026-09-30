# Salescope model card

## Intended use

Exploratory daily net-revenue forecasting for a portfolio demo or a small uploaded sales dataset. One segment is modeled per run. The tool supports planning discussions; it does not establish causal effects or guarantee revenue.

## Candidates and fixed settings

- Seasonal baseline: repeat the previous matching weekday recursively; a last-observation fallback exists for histories shorter than seven days, although app eligibility requires more history.
- NumPy Ridge: features are standardized on each training prefix and a closed-form ridge solution is fit with alpha=10 and an unregularized intercept.
- NumPy gradient boosting: 40 squared-error regression trees, depth 2, 16 candidate quantile splits per feature, learning_rate=0.075, leaf L2 regularization=10, and at least 12 rows in each leaf.

The first release compares these fixed configurations rather than running an expensive hyperparameter search. The models use NumPy directly and avoid a scikit-learn/SciPy dependency, keeping Vercel's runtime bundle small. See run metadata for the model implementation and feature names.

## Data and features

Daily net revenue in one declared currency. Optional dimensions select subsets. Inputs are lagged revenue at 1, 7, 14, and 28 days, shifted 7/28-day rolling means, shifted 7-day standard deviation, cyclic weekday/year signals, and a trend index. Ridge scaling is fitted only to training data. The initial 28 days supply feature history.

Missing dates require explicit handling. Returns remain negative. Forecasts are not clipped because a blanket non-negative constraint would contradict the net-revenue target. Products with intermittent sales may be better served by specialized demand models in a future release.

## Evaluation

For history length N and horizon H:

- Validation origins: N−4H, N−3H, N−2H; each predicts a full H-day period.
- Final untouched test: N−H through N−1.
- Model selection: lowest pooled MAE over the three equal-length validation windows; ties use stable candidate ordering.
- Final evaluation: selected model and baseline fitted on the prefix ending before the test.
- Deployment fit: selected model trained again using all N observations.

The final test is never used to choose a model, tune settings, or estimate intervals. Recursive evaluation consumes its own predictions within the horizon. A previous test-suite run mutated the final actuals to verify these boundaries. A stable split strategy supports reproducibility, subject to numerical differences across platforms.

MAE, RMSE, and WAPE are reported; WAPE uses sum(abs(actual)) as denominator and is unavailable if zero. Final-test baseline improvement can be negative. The application reports that result honestly without switching models after seeing the test.

## Uncertainty

For the selected model, collect absolute errors for each horizon at 20 evenly spaced earlier origins, whose forecast windows end before the final test. Use the empirical 80th percentile (higher order statistic) as the symmetric radius for that horizon. Origins can overlap and are not independent. Short data can provide fewer than 20 distinct origins, in which case bands are withheld.

These are approximate empirical ranges, not conformal coverage guarantees. Coverage is measured on the untouched final test; report both the nominal 80% level and actual observed coverage. Model selection and calibration reuse parts of the earlier development period, so uncertainty estimates may be optimistic. A future business deployment should use separate calibration data and more extensive rolling tests.

Individual daily bands cannot be summed into a probability interval for the total. A prediction of zero or negative values is permitted, and the application does not estimate stock availability or lost demand.

## Limitations

- Synthetic demonstration data cannot establish real-world accuracy.
- Long recursive horizons accumulate forecast errors.
- New promotions, prices, holidays specific to a locality, stockouts, and external shocks are not modeled explicitly.
- Annual seasonality estimates are weak with short histories.
- Segment forecasts are independent and are not reconciled to an aggregate total.
- Net revenue may reflect refunds rather than demand; inventory decisions require an appropriate unit-demand model.
- Default demo history ends in 2025; forecasts begin after the last record, not the current calendar date.
- No scheduled retraining, database integration, authentication, drift alerting, or production SLA is included.

## Refresh policy

Users explicitly retrain after loading new records or changing the scope. The data identity and configuration are stored with each result, and mismatched results are hidden from reports. Review errors against newly observed sales before using forecasts for consequential decisions.

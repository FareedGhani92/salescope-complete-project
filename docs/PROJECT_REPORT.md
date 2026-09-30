# Salescope: Sales Prediction Dashboard

## Abstract

Salescope is an interactive sales analytics and forecasting application developed with Streamlit. It combines file ingestion, validation, exploratory analysis, forecasting, evaluation, and exports within one workflow. The demonstration dataset is synthetic; the project demonstrates implementation quality and evaluation methodology without claiming validated commercial forecasting performance.

## Problem and objective

Sales records are often available as spreadsheets, but raw tables make trends and future expectations difficult to assess. The project aims to make those records understandable and produce forecasts whose historical performance can be inspected. The application emphasizes chronological evaluation, explicit data assumptions, and reproducible results.

## Functional requirements and implementation

| Requirement | Implementation |
|---|---|
| Immediate demonstration | Reproducible three-year retail dataset |
| CSV/XLSX input | Bounded upload, first-sheet workbook import, column mapping |
| Data quality | Invalid-row reporting, optional duplicate removal, missing-date policy, return preservation |
| Historical analysis | Revenue KPIs, temporal trends, product rankings, weekday and store comparisons |
| Forecasting | Seasonal baseline, native NumPy Ridge, and native NumPy gradient-boosted trees; 7/30/90-day horizons |
| Evaluation | Three chronological validation windows plus final untouched test |
| Uncertainty | Empirical per-horizon error ranges and measured final-test coverage |
| Reporting | CSV, Excel, Markdown report, and cleaning summary |
| Reproducibility | Seed, dataset identity, settings, date boundaries, model and Python versions |
| Deployment | Pinned dependencies, Streamlit configuration, Dockerfile, CI workflow |

## Architecture

The Streamlit presentation layer coordinates session state and user controls. Independent modules handle ingestion/cleaning, synthetic data, chart generation, forecasting, and exports. Data flows from upload through validation and daily aggregation, then into historical analysis or model evaluation. The selected model is refitted for future forecasting. Exports use the same result objects displayed on screen.

Uploaded data stays in session memory. The application has no durable user database. Only synthetic demo data is shared through Streamlit's data cache. Changes to dataset identity or forecast configuration prevent a stale result from appearing as current.

## Methodology

The target is daily net sales revenue in a declared single currency. Features use only preceding observations plus calendar information known in advance. Three model configurations are compared on full forecast windows. Forecasts recursively use predicted values when actual future lags are unavailable. Final-test data is withheld from selection and interval estimation.

This release deliberately uses documented fixed configurations rather than a large parameter search. The forecasting models use NumPy directly, avoiding the SciPy and scikit-learn packages in the Vercel function bundle. Future development could add bounded tuning using nested chronological validation.

## Demonstration results

Measured on the included synthetic data on September 30, 2026, after moving the models to native NumPy implementations:

| Horizon | Selected model | Final-test MAE (USD/day) | Baseline MAE | WAPE | Empirical range coverage |
|---|---|---:|---:|---:|---:|
| 30 days | Ridge regression | 4,055.79 | 3,597.98 | 9.06% | 26.7% |

On this synthetic holdout, the selected model is 12.7% worse than the seasonal baseline, and the empirical interval reaches only 26.7% observed coverage against an 80% nominal target. These results are displayed honestly in the app and model card. They are demonstration results, not claims about unseen business data.

The updated 30-day demo preparation completed in approximately 0.59 seconds locally; actual hosting performance depends on CPU, load, dataset length, and cold-start conditions. Earlier measurements in `TEST_REPORT.md` predate the NumPy-native model change.

## Testing

Tests cover file formats, invalid values, duplicate policy, date gaps, order metrics, aggregation, lag construction, recursive baseline behavior, forecast boundaries, zero-sales series, minimum history, downloads, and all six pages. A dedicated leakage test modifies all final-test actual values and verifies that selection, test predictions, and pre-test bands remain unchanged. UI tests also verify forecast navigation, currency invalidation, empty combinations, and sample restoration.

The local test suite passed. See TEST_REPORT.md for the final verification record and unverified deployment boundaries.

## Limitations and future work

Synthetic data, recursive error accumulation, empirical ranges with overlapping calibration origins, and omitted future business drivers limit predictive reliability. The project does not reconcile segment forecasts, estimate causal promotion effects, or forecast inventory demand from net revenue. Production extensions include authenticated access, durable data storage, scheduled ingestion, drift monitoring, calibration improvements, and specialized intermittent-demand models.

## References

- [Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit app testing](https://docs.streamlit.io/develop/api-reference/app-testing)
- [scikit-learn time-series forecasting example](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html)
- [TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)

The implementation uses explicit chronological windows to reproduce full-horizon recursive forecasts, rather than directly applying TimeSeriesSplit to independently scored rows.

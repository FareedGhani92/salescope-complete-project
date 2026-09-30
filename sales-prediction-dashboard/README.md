# Salescope — Sales Prediction Dashboard

A complete sales analytics and forecasting project with an original Streamlit app and a Vercel-ready browser app. Built as a portfolio project with honest evaluation, an immediately usable demo, and no paid API requirement.

## Run the original Streamlit edition locally

Use **Python 3.13**. Open a terminal inside this project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-streamlit.txt
python -m streamlit run app.py
```

On Windows, use `python` instead of `python3` and activate with `.venv\Scripts\activate`.
On macOS, `run.command` performs setup and starts the app. The first launch downloads dependencies.
Open the local URL printed by Streamlit. No database, API key, or login is required.

## Features

- Six pages: Overview, Sales analysis, Forecast studio, Model performance, Data workspace, and Reports & guide.
- Deterministic sample data: 19,728 daily product/store records, six products, three stores, 2023–2025.
- CSV and Excel import with column mapping, validation, cleaning summary, and rejected-row downloads.
- Date, category, store, and product filters; totals, averages, weekday patterns, and revenue comparisons.
- Three candidates: weekly seasonal baseline, native NumPy Ridge regression, and small native NumPy gradient-boosted trees.
- True recursive 7-, 30-, and 90-day forecasts with chronological validation and a separate final test.
- MAE, RMSE, WAPE, baseline comparisons, and measured coverage of empirical uncertainty ranges.
- Forecast CSV, formatted Excel workbook, model-comparison CSV, and a Markdown summary report.
- Session-scoped uploaded data and automatic detection of outdated forecast settings.
- Unit, forecasting-leakage, export, Streamlit interaction, and FastAPI integration tests; GitHub Actions workflow; Dockerfile.

## Run the Vercel edition locally

The Vercel edition separates a responsive HTML/CSS/JavaScript dashboard from its stateless FastAPI backend and shares the forecasting core with Streamlit. The dashboard checks `/api/health` and shows whether the forecast service is available. It starts with the bundled 19,728-row synthetic sample at `public/data/sample_sales.csv`; it needs no database or database credentials. There is no admin login or application sign-in. Install the development requirements once, then start the local preview:

```bash
python -m pip install -r requirements-dev.txt
python -m uvicorn main:app --reload --port 8502
```

Open `http://127.0.0.1:8502`. Streamlit continues to run separately on its usual port. The browser reads CSV/XLSX data locally; only daily totals are submitted when a forecast is requested. Imported data and results clear on refresh.

## Publish your portfolio demo

### Vercel

Use [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) to deploy the browser-based edition. It uses Python Functions for forecasting and exports, and Vercel's static CDN for the dashboard. The original Streamlit edition remains in the project and can still be run locally or published separately.

The Vercel function uses a small dependency set and excludes scikit-learn, SciPy, Streamlit, and Plotly. After `vercel build`, run `python scripts/check_vercel_size.py` to verify that each generated function stays below the 225 MB deployment budget.

### Streamlit hosting

Upload the **contents of this directory** to a GitHub repository, then deploy `app.py` on Streamlit Community Cloud using Python 3.13. The Streamlit host installs `requirements-streamlit.txt` (or use the root requirements and add the Streamlit extras) and reads `.streamlit/config.toml`.

Follow [the deployment guide](docs/DEPLOYMENT.md) for exact steps. A hosted URL is created by your hosting account; the project does not contain a pre-created public deployment.

## Try the complete workflow

1. Open Overview. The synthetic retail dataset is already active.
2. Filter to one store or product, or keep all sales.
3. Open Forecast studio and select the next 30 days.
4. Click Generate forecast.
5. Read the historical errors on Model performance.
6. Download the Excel report from Reports & guide.
7. To replace sample data, use Data workspace and map at least date and sales.

The sample ends on December 31, 2025. Its forecast therefore begins on January 1, 2026, regardless of the current date. Upload newer history to forecast beyond its latest recorded day.

## Input contract

Required columns (names can be mapped):

```csv
date,sales
2025-01-01,1200.50
2025-01-02,1350.00
```

Optional fields: product, category, store, region, quantity, order_id, promotion.
Sales means **net revenue in one currency**. The currency control changes labels; it does not perform conversion. Do not mix currencies in an upload. Order IDs must be globally unique per order. The application computes average order value only when every selected row has an order ID.

Limits: 20 MB, 100,000 rows, one worksheet (the first) for XLSX, and a maximum date span of 20 years. Numeric Excel date serials must be exported as calendar dates. Sales must be numeric without symbols or thousands separators. Timezone-aware dates are normalized to UTC before daily aggregation; pre-convert business dates if another timezone is needed.

Missing dates are unknown by default. Enable “Missing days mean zero sales” only when this is true for the selected segment. Exact duplicate mapped rows are retained unless explicitly removed. Returns and negative net revenue are preserved.

| Forecast | Minimum complete daily history |
|---|---:|
| 7 days | 140 days |
| 30 days | 232 days |
| 90 days | 472 days |

These minimums reserve 112 initial training days, three validation windows, and one final test window. They are eligibility thresholds, not promises of quality.

## How the forecasting works

1. Aggregate the selected segment to a complete daily series.
2. Reserve the last H days as the final test period.
3. Compare fixed, documented model configurations on three preceding H-day validation windows.
4. Select the lowest validation MAE; the seasonal baseline is allowed to win.
5. Evaluate the selected model and baseline on the reserved test period.
6. Estimate per-horizon error ranges from 20 earlier rolling origins, excluding the final test.
7. Refit on all available history and recursively predict H future days.

Each prediction sees only history available at its origin. Lagged features inside a multi-day forecast use predictions, never actual future sales. The leakage test changes the entire final period and verifies that model selection, test predictions, and pre-test error ranges do not change.

Features: lags 1/7/14/28, prior 7/28-day means, prior 7-day standard deviation, cyclic weekday/year signals, and a trend index. Future prices, promotions, stockouts, and external events are not supplied to the model.

See [MODEL_CARD.md](docs/MODEL_CARD.md) for uncertainty assumptions and limitations.

## Verify or regenerate

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/prepare_demo.py
```

The regeneration script recreates `data/sample_sales.csv` plus a demonstration model, metadata, forecast, comparison table, and report under `artifacts/`. The app trains fresh models for each session and does not deserialize user-uploaded models. The demo artifact uses joblib and is generated only for local portfolio materials; joblib is not a Vercel runtime dependency.

## Project structure

```text
main.py                        FastAPI/Vercel entry point
api/forecast.py                Stateless prediction endpoint
api/report.py                  Excel report endpoint
public/                        Vercel dashboard, sample, and browser assets
vercel.json, pyproject.toml     Vercel runtime and static setup
app.py                         Streamlit interface and session workflow
src/data.py                    Import, cleaning, aggregation, metrics
src/demo.py                    Deterministic synthetic data generator
src/forecast.py                Models, chronological evaluation, intervals
src/charts.py                  Plotly visualizations
src/reports.py                 Safe CSV, Excel, and summary exports
data/sample_sales.csv          Ready-to-use demonstration data
scripts/prepare_demo.py         Recreate demo data and model artifacts
artifacts/                     Demonstration outputs and model metadata
tests/                         Data, forecasting, export, and UI tests
docs/                          Deployment, user guide, project report, model card
.github/workflows/tests.yml    Automated checks on GitHub
.streamlit/config.toml         Theme, upload limit, telemetry preference
pyproject.toml                 Vercel/uv project metadata and runtime dependencies
requirements.txt               Matching pip requirements for local runs
requirements-streamlit.txt     Streamlit local app dependencies
Dockerfile                     Alternative container deployment
run.command                    macOS setup and launch helper
```

## Data handling and production scope

Uploaded data and fitted models are kept in the active server session, not intentionally persisted to disk or a database. Only the bundled synthetic dataset is globally cached. Session disposal is controlled by Streamlit; a browser refresh can lose work. Download reports before leaving.

The app makes no external AI API calls. Fonts may load from Google Fonts; system fonts are used as a fallback. This public-portfolio configuration has no application-level login, durable user storage, scheduled retraining, or audit trail. Those require a separate production setup before using confidential business data. Resource limits reduce accidental load but are not a full abuse-prevention system.

## Portfolio description

> Built Salescope, an end-to-end sales analytics and forecasting application with Python, Streamlit, FastAPI, pandas, NumPy, and Plotly. Implemented validated CSV/Excel ingestion, recursive multi-day forecasts, chronological model evaluation, empirical uncertainty ranges, and downloadable reports, supported by automated checks and deployment configuration.

Use the measured results in `artifacts/demo_metadata.json` only with the explicit qualification that they come from synthetic demonstration data.

## License

MIT. The included sales data is generated synthetically by this project.

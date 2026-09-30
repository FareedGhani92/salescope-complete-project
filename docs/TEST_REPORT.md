# Verification record

Historical verification: this report records the September 27 implementation, before the September 30 switch from scikit-learn estimators to native NumPy models. The reported 34-test pass and forecast metrics do not certify the later model implementation. The NumPy-native update was syntax-checked and its sample artifacts were regenerated; a fresh automated suite was not run.

## Frontend and API verification — October 1, 2026

The current suite passes **37 tests**. Three API integration checks cover the served dashboard and bundled sample, health response, a complete forecast request followed by an Excel report download, and rejection of a date gap. This uncovered and fixed a report request mismatch between the frontend and the strict backend schema.

Python compilation, JavaScript syntax, mirrored frontend assets, and `vercel.json` parsing also pass. The automated browser-server launch was unavailable in the restricted local environment; the ASGI integration tests exercise the real FastAPI routing and static-file mount without binding a network port. No Vercel cloud deployment was performed.

Date: September 27, 2026. Environment: local macOS arm64, Python 3.13.15, exact direct dependencies in requirements.txt.

## Automated checks

`python -m pytest -q --disable-warnings`: **34 passed**.

Covered behavior:

- CSV/XLSX round trips, malformed/empty files, row limits, numeric-date rejection.
- Required mapping, invalid/non-finite sales, negative revenue, optional quantities, duplicates.
- Explicit missing-day handling, distinct orders, sample-data totals, dataset identities.
- Past-only lag features, recursive weekly baseline, chronological model selection.
- Final-test mutation proves that selection, test predictions, and calibration ranges do not consume final-test actuals.
- Correct forecast dates and lengths, all-zero sales, minimum histories, irregular dates.
- Excel workbook contents, matching CSV values, reproduction metadata, formula-safe text export.
- All six Streamlit pages, empty filter combinations, dataset restoration, forecast workflow, cross-page result retention, and currency invalidation.

`python -m pip check`: no broken requirements found.

Third-party warnings observed: pandas/NumPy datetime deprecation notices and a restricted-environment physical-core detection fallback. They do not fail the tests; direct versions are pinned. Recheck compatibility before upgrading packages.

## Live browser checks

- Application loaded at local port 8501 with the synthetic demo.
- Overview totals, sales analysis charts, and forecasting controls rendered.
- The live browser generated a 30-day forecast and displayed predictions, evaluation error, and observed interval coverage.
- Forecast CSV download succeeded. The downloaded file was read back: 30 rows, starting 2026-01-01, with model, currency, training cutoff, and forecast fields.
- At a 390-pixel viewport, document width matched viewport width and forecast metric cards stacked at 358 pixels wide, with no page-level horizontal overflow.
- The browser viewport override was reset afterward.

Screenshot capture was unavailable through the connected browser, so no screenshot-based visual sign-off is claimed. User-file ingestion and Excel exports were verified automatically; the entire browser upload-dialog journey was not separately exercised.

## Forecast smoke checks

All three horizons executed on the complete demo:

| Horizon | Selected model | Final-test MAE | Measured runtime |
|---|---|---:|---:|
| 7 days | Ridge regression | 1,120.22 USD | ~0.37 s |
| 30 days | Gradient boosting | 2,693.60 USD | ~1.58 s including demo generation/artifact preparation |
| 90 days | Gradient boosting | 3,008.57 USD | ~1.60 s |

Timing is a local observation, not a hosting SLA. Synthetic-data performance does not predict real-world accuracy. The 30-day interval's measured 60% coverage is below the nominal 80% and is clearly disclosed in the application and model card.

## Deployment boundaries

The local application is running and the repository is prepared for Streamlit Community Cloud. No public deployment or GitHub repository was created. The supplied GitHub Actions workflow and Dockerfile have not been executed on their target platforms in this session. Perform the deployment guide's fresh-session smoke test after publishing.

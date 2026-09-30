# Publish Salescope on Vercel

Salescope includes a browser-dashboard edition for Vercel alongside its original Streamlit edition. The Vercel app uses a static frontend plus a Python FastAPI function; the forecasting logic is shared with Streamlit.

## Deploy from GitHub

1. Put the contents of this project folder at the root of a GitHub repository. Confirm that `main.py`, `pyproject.toml`, `requirements.txt`, `vercel.json`, and `public/` are at the repository root. Vercel resolves the runtime dependencies from the `[project]` table in `pyproject.toml`; `requirements.txt` is kept in sync for local pip installs.
2. Sign in to [Vercel](https://vercel.com/) and choose **Add New → Project**.
3. Import that GitHub repository. If it is a portfolio monorepo, set the project root directory to this Salescope project folder.
4. Keep Vercel's detected FastAPI framework and Python 3.13 version. The project entry point is `main.py`; do not disable framework detection or select the Streamlit `app.py` as the entry point.
5. Deploy. After the first build, open the generated `*.vercel.app` URL and try the overview, a sample forecast, and the Excel report download.

Vercel creates preview deployments from other branches and production deployments from the configured production branch. Connect a custom domain from the project settings if you own one.

## Deploy from the command line

From the project root, sign in to Vercel and link a project once, then deploy a preview:

```bash
python -m pip install -r requirements.txt
vercel login
vercel link
vercel deploy
```

After checking the preview, publish the production deployment with `vercel deploy --prod`.

## What is deployed

- `public/index.html`, CSS, JavaScript, sample CSV, and the locally bundled SheetJS parser are static assets.
- The root URL redirects to `/index.html`, which Vercel serves from the static CDN.
- `main.py` serves `/api/forecast`, `/api/report`, and health endpoints as one FastAPI Python Function. Vercel applies the function-duration limit for your selected plan.
- The `[project].dependencies` list in `pyproject.toml` contains only the packages used by the Python function. The heavier Streamlit and Plotly packages remain in `requirements-streamlit.txt`.
- The included 19,728-row synthetic dataset is served as a static file from `public/data/sample_sales.csv` and loads automatically when the dashboard opens.
- No model file, secrets, environment variables, database connection, database credentials, admin login, or paid AI provider is required. The Vercel edition has no application authentication.

The function uses NumPy-native forecasting and excludes scikit-learn and SciPy. The direct Python runtime dependencies occupy 117.3 MB in the local Python 3.13 environment. Vercel builds Linux wheels, so use its build output for the authoritative size check: after `vercel build`, run `python scripts/check_vercel_size.py`. It checks each generated function against a conservative 225,000,000-byte budget.

## Data flow and limits

Uploads are parsed and filtered in the browser. The raw CSV/XLSX is not posted to Vercel. Generating a forecast sends one daily aggregated value per date (up to 7,305 days), the selected horizon, and display labels. The Python API does not store that request. Exporting an Excel report sends the generated forecast and evaluation summary back to a separate request so the workbook can be created. Browser memory is cleared by a page refresh.

The browser accepts CSV and XLSX files up to 20 MB and 100,000 records. The API limits request bodies to 1 MB, validates complete daily dates, and supports 7-, 30-, and 90-day horizons. Minimum histories are 140, 232, and 472 complete days respectively. All values in one upload must use the same currency; the currency selector changes labels and does not convert amounts. The included demo data is synthetic.

Vercel's Python runtime and function-duration availability can depend on current platform limits and account plan. If a 90-day request is near the selected plan's execution limit, lower the horizon or run the project on a host with a longer function window. Forecast estimates do not include planned promotions, future prices, stockouts, or outside events. This portfolio demo has no sign-in, persistent storage, or production controls for confidential business data.

## Troubleshooting

- **The page is blank:** check that `public/index.html` exists at the Vercel project root and that the output directory is not overridden in project settings.
- **The sample does not load:** verify `/data/sample_sales.csv` is present in the deployed `public/data/` folder.
- **Forecast API returns a 500:** inspect the Vercel Function logs; confirm the `main:app` entry point and `requirements.txt` were included.
- **Forecast takes too long:** try 7 or 30 days to confirm the deployment and plan's function duration. The full chronological evaluation does more work for longer horizons.
- **Upload rows are rejected:** map date and sales explicitly, use parseable calendar dates and numeric sales, then review the rejected-row count.

## References

- [Vercel FastAPI deployment](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python)
- [Vercel project configuration](https://vercel.com/docs/project-configuration/vercel-json)

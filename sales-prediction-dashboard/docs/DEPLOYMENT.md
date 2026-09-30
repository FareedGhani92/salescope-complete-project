# Put Salescope online

## Recommended: Streamlit Community Cloud

You need your own GitHub account and Streamlit Community Cloud account. No AI API key is required.

1. Create a GitHub repository named `sales-prediction-dashboard` (or another name you prefer).
2. Add the contents of this project folder to the repository root. Include hidden `.streamlit/` and `.github/` directories. Do not upload `.venv/`, private sales files, credentials, or cache directories.
3. Confirm the root contains `app.py`, `requirements.txt`, and `src/`. Keep `data/sample_sales.csv` so the demo is immediately available; the app can also generate it if missing.
4. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/).
5. Choose **Create app**, select your repository and branch, and set the entry-point path to `app.py`.
6. In advanced settings, select **Python 3.13**, matching the tested local environment. No secrets are needed.
7. Choose an available app URL and deploy.
8. Wait for installation and startup to finish, then open your assigned HTTPS URL.
9. Test Overview, a 7-day forecast, Model performance, and one report download in a fresh browser session.
10. Add the verified public URL to your GitHub description, portfolio, and résumé.

If you upload the entire folder as a nested directory instead, use the actual nested entry-point path and ensure dependency/configuration discovery is correct. Keeping the app at repository root is simpler.

Official instructions: [Deploy your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Updating the deployed app

Commit updates to the connected branch. Review deployment logs, then repeat the short smoke test. Run the test suite before changing models or dependencies. Pin and test dependency updates together; do not independently upgrade a saved model's runtime and expect identical results.

## Optional Docker deployment

From the repository root:

```bash
docker build -t salescope .
docker run --rm -p 8501:8501 salescope
```

Open `http://localhost:8501`. The container binds to port 8501 and includes a health check. For another hosting service, route HTTPS traffic to that port and enable WebSocket support. Some platforms require a dynamic port; adapt the start command to their documented requirements.

The Docker configuration is supplied; a container build must be verified in your Docker/hosting environment before relying on it.

## Common problems

| Symptom | Resolution |
|---|---|
| `ModuleNotFoundError` | Install from `requirements.txt`; confirm deployment starts from the repository root |
| Python/dependency install failure | Select Python 3.13; read the first actual package installation error in the logs |
| Forecast button disabled | Supply more daily history, broaden filters, or select a shorter horizon |
| Missing-days message | Correct the source data, or confirm absent dates were zero-sales days |
| No current forecast in Reports | Generate it again for the current dataset, currency, filters, and horizon |
| App sleeps or restarts | Reopen it; session uploads and models may need to be recreated |
| Uploaded Excel file fails | Use a valid `.xlsx`, put data in the first worksheet, or export a UTF-8 CSV |
| Mixed currencies | Split the dataset into one currency or convert it before upload |

## Release checklist

- Tests pass in the deployment-compatible environment.
- Only synthetic/demo data is included publicly.
- The app loads in a fresh, signed-out browser session as intended.
- Forecasts and report downloads work after deployment.
- The portfolio link is the hosted HTTPS URL, not a localhost address.
- Results are labeled synthetic; forecast limitations remain visible.

For the updated Vercel deployment path, see [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md).

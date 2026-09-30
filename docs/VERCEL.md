# Vercel deployment assessment

Initial assessment, September 29, 2026. On September 30, a separate browser-based Vercel edition was added. See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for the current setup and publish steps.

## Current status

The original Streamlit application has not been deployed to Vercel. Streamlit still uses server-session memory for uploads and fitted models. A separate Vercel edition now exists in `public/` with its stateless FastAPI application in `main.py`; it has not yet been deployed or connected to a Vercel project.

Vercel now supports Python ASGI applications and Python WebSocket endpoints with Fluid compute. Streamlit 1.64 also provides an ASGI-compatible `st.App`. Therefore, older advice that Vercel never supports Python or WebSockets is no longer accurate. This does not, by itself, verify reliable hosting for the complete Salescope workflow.

## Compatibility issues to resolve

| Existing behavior | Vercel consideration |
|---|---|
| Uploaded data and models live in Streamlit session memory | WebSocket connections end at the function duration limit; reconnects can reach a different instance |
| Upload and download HTTP requests accompany the session WebSocket | Streamlit documents a need for session affinity or shared storage across replicas; otherwise uploads and generated media can fail |
| Uploads up to 20 MB | The documented function request/response body limit is 4.5 MB; large uploads require a different transport/storage approach |
| Python function dependencies | The Vercel edition installs NumPy, pandas, openpyxl, and FastAPI plus their runtime dependencies. Scikit-learn, SciPy, Streamlit, and chart libraries are excluded from this function. Run `python scripts/check_vercel_size.py` after `vercel build` to check every built function against the 225 MB project budget. |
| Existing start command is `streamlit run app.py` | Vercel expects an exported supported application entrypoint, not this Docker startup command |

The application should not be labeled Vercel-ready simply by adding a redirect or configuration file.

## Vercel edition now implemented

The Vercel edition preserves the current Streamlit project and shares the forecasting and reporting code. It provides:

- Six responsive browser pages for overview, analysis, forecasting, performance, data and reports.
- In-browser CSV/XLSX parsing and filtering. Only aggregated daily sales reach the forecasting function.
- Same-origin forecast and Excel report endpoints with bounded request sizes.
- Lightweight Python requirements separated from the Streamlit dependencies.
- A function bundle budget check that fails if any built function exceeds 225,000,000 bytes.
- Deployment configuration and steps in [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md).

The outstanding publish step requires signing in to the user's Vercel account and creating a project deployment. A deployed URL and cloud runtime behavior cannot be claimed before that account step and a live verification.

This changes the UI framework. The original Streamlit edition remains available for the original project requirement and Streamlit-compatible hosting.

## If the project must remain Streamlit

Use a host designed to run the Streamlit server, such as Streamlit Community Cloud, following DEPLOYMENT.md. A separate Vercel portfolio site can link to that application, but that is not the same as hosting the application itself on Vercel.

## References

- [Vercel Python runtime and entrypoints](https://vercel.com/docs/functions/runtimes/python)
- [Vercel WebSockets and reconnection behavior](https://vercel.com/docs/functions/websockets)
- [Vercel function limits](https://vercel.com/docs/functions/limitations)
- [Streamlit session affinity and replicated deployments](https://docs.streamlit.io/develop/concepts/architecture/architecture)
- [Streamlit ASGI application API](https://docs.streamlit.io/1.60.0/develop/api-reference/server/st.app)

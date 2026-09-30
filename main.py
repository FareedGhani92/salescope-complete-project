"""Vercel entry point for the static Salescope frontend and stateless API."""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.forecast import router as forecast_router
from api.report import router as report_router

app = FastAPI(title="Salescope", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(forecast_router)
app.include_router(report_router)
PUBLIC_DIR = Path(__file__).resolve().parent / "public"


@app.get("/", include_in_schema=False)
def dashboard_home():
    # Serve the portfolio page from the function so it works even when a CDN
    # static-file route is not configured for the Vercel project.
    return FileResponse(PUBLIC_DIR / "index.html", media_type="text/html")


@app.middleware("http")
async def request_limits_and_headers(request: Request, call_next):
    size = request.headers.get("content-length")
    try:
        too_large = size is not None and int(size) > 1_000_000
    except ValueError:
        too_large = True
    if too_large:
        return JSONResponse({"detail": "Request is too large."}, status_code=413,
                            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


# Serve the frontend and its assets from the same function as the API.
app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="frontend")

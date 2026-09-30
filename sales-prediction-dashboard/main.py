"""Vercel entry point for the static Salescope frontend and stateless API."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.forecast import router as forecast_router
from api.report import router as report_router

app = FastAPI(title="Salescope", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(forecast_router)
app.include_router(report_router)


@app.get("/", include_in_schema=False)
def dashboard_home():
    # Vercel serves public files from its CDN; send the root path to its index.
    return RedirectResponse(url="/index.html", status_code=307)


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


# Vercel promotes this directory to its static CDN. Mounting it here also gives
# developers a same-origin local preview via `uvicorn main:app`.
app.mount("/", StaticFiles(directory="public", html=True), name="frontend")

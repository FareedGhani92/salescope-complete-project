"""Stateless forecast endpoint. Only aggregated daily values reach this API."""
from __future__ import annotations

from datetime import date
import math

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from src.forecast import HORIZONS, run_forecast

router = APIRouter()


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    sales: float = Field(allow_inf_nan=False)


class ForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    points: list[Point] = Field(min_length=140, max_length=7305)
    horizon: int = Field(ge=7, le=90)
    currency: str = Field(default="USD", min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    scope: str = Field(default="All sales", max_length=320)


@router.get("/api/health")
def health():
    return {"status": "ok", "model_horizons": list(HORIZONS)}


@router.post("/api/forecast")
def forecast(payload: ForecastRequest):
    if payload.horizon not in HORIZONS:
        raise HTTPException(422, "Choose a 7, 30, or 90 day forecast.")
    dates = [point.date for point in payload.points]
    if any(right.toordinal() - left.toordinal() != 1 for left, right in zip(dates, dates[1:])):
        raise HTTPException(422, "The selected sales must have one complete record for every day.")
    series = pd.Series([point.sales for point in payload.points], index=pd.to_datetime(dates),
                       name="sales", dtype=float)
    try:
        result = run_forecast(series, payload.horizon, currency=payload.currency,
                              scope=payload.scope, data_id="browser-aggregate")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    validation = result.comparison.rename(columns={"Model": "model", "MAE": "Validation MAE"})
    selected = result.model_name
    comparison = []
    for row in validation.to_dict("records"):
        comparison.append({"model": row["model"], "Validation MAE": row["Validation MAE"],
            "Validation RMSE": row.get("RMSE"), "Validation WAPE (%)": row.get("WAPE (%)"),
            "Test MAE": result.metrics["MAE"] if row["model"] == selected else None,
            "Test WAPE (%)": result.metrics["WAPE (%)"] if row["model"] == selected else None,
            "Status": "Selected" if row["model"] == selected else row.get("Status", "Evaluated")})
    return {
        "model": result.model_name,
        "forecast": result.forecast.assign(date=lambda f: f.date.dt.strftime("%Y-%m-%d")).to_dict("records"),
        "comparison": comparison,
        "test": result.test.assign(date=lambda f: f.date.dt.strftime("%Y-%m-%d")).to_dict("records"),
        "metrics": result.metrics,
        "metadata": result.metadata,
    }

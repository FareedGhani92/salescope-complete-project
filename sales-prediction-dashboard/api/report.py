"""Build a bounded Excel download from the result already held in the browser."""
from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import StreamingResponse

from src.reports import excel_report

router = APIRouter()


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    forecast: list[dict] = Field(min_length=7, max_length=90)
    comparison: list[dict] = Field(min_length=1, max_length=3)
    test: list[dict] = Field(min_length=7, max_length=90)
    metrics: dict
    metadata: dict


@router.post("/api/report")
def report(payload: ReportRequest):
    horizon = payload.metadata.get("horizon_days")
    if horizon not in (7, 30, 90) or len(payload.forecast) != horizon or len(payload.test) != horizon:
        raise HTTPException(422, "Forecast, test, and horizon must agree.")
    try:
        forecast = pd.DataFrame(payload.forecast)
        forecast["date"] = pd.to_datetime(forecast["date"], errors="raise")
        test = pd.DataFrame(payload.test)
        test["date"] = pd.to_datetime(test["date"], errors="raise")
        result = SimpleNamespace(forecast=forecast, test=test, comparison=pd.DataFrame(payload.comparison),
                                 metrics=payload.metrics, metadata=payload.metadata)
        workbook = excel_report(result)
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(422, "Report values are incomplete or invalid.") from exc
    return StreamingResponse(BytesIO(workbook),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="salescope_report.xlsx"', "Cache-Control": "no-store"})


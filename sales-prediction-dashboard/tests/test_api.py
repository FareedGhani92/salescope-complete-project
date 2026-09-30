import asyncio
import json

from main import app
from src.data import make_daily


def request(method, path, payload=None):
    body = json.dumps(payload).encode() if payload is not None else b""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"content-type", b"application/json")] if body else [],
        "server": ("testserver", 80),
        "client": ("testclient", 50000),
        "state": {},
    }
    events = []
    received = False

    async def receive():
        nonlocal received
        if received:
            return {"type": "http.disconnect"}
        received = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(event):
        events.append(event)

    asyncio.run(app(scope, receive, send))
    start = next(event for event in events if event["type"] == "http.response.start")
    response_body = b"".join(event.get("body", b"") for event in events
                               if event["type"] == "http.response.body")
    headers = {key.decode().lower(): value.decode() for key, value in start["headers"]}
    return start["status"], headers, response_body


def test_frontend_health_and_bundled_demo_are_served():
    status, headers, _ = request("GET", "/")
    assert status == 307
    assert headers["location"] == "/index.html"

    status, _, body = request("GET", "/index.html")
    assert status == 200
    assert b"Salescope" in body

    status, _, body = request("GET", "/api/health")
    assert status == 200
    health = json.loads(body)
    assert health["status"] == "ok"
    assert health["model_horizons"] == [7, 30, 90]

    status, _, body = request("GET", "/data/sample_sales.csv")
    assert status == 200
    assert body.startswith(b"date,sales,")
    assert len(body.splitlines()) == 19_729


def test_forecast_and_excel_report_work_end_to_end(demo):
    daily = make_daily(demo)
    points = [
        {"date": day.strftime("%Y-%m-%d"), "sales": float(sales)}
        for day, sales in daily.items()
    ]
    status, _, body = request(
        "POST", "/api/forecast",
        {"points": points, "horizon": 7, "currency": "USD", "scope": "All sales"},
    )

    assert status == 200, body
    result = json.loads(body)
    assert len(result["forecast"]) == 7
    assert len(result["test"]) == 7
    assert result["metadata"]["model_implementation"] == "NumPy native v1"
    assert result["forecast"][0]["date"] == "2026-01-01"

    report_payload = {key: result[key] for key in ("forecast", "comparison", "test", "metrics", "metadata")}
    status, headers, report = request("POST", "/api/report", report_payload)
    assert status == 200, report
    assert headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert report.startswith(b"PK")


def test_forecast_api_rejects_missing_days(demo):
    daily = make_daily(demo).iloc[:160]
    points = [
        {"date": day.strftime("%Y-%m-%d"), "sales": float(sales)}
        for day, sales in daily.items()
    ]
    points[20]["date"] = points[19]["date"]

    status, _, body = request("POST", "/api/forecast", {"points": points, "horizon": 7})
    assert status == 422
    assert "complete record for every day" in json.loads(body)["detail"]

"""Regenerate sample data and a trusted, optional demonstration model artifact."""
from pathlib import Path
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import joblib
from src.demo import generate_demo
from src.data import make_daily, fingerprint
from src.forecast import run_forecast
from src.reports import forecast_export, summary_report

if __name__ == "__main__":
    start = time.perf_counter()
    data = generate_demo()
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "artifacts").mkdir(exist_ok=True)
    data.to_csv(ROOT / "data/sample_sales.csv", index=False, date_format="%Y-%m-%d")
    result = run_forecast(make_daily(data), 30, data_id=fingerprint(data))
    result.metadata["data_source"] = "Synthetic retail demo"
    result.metadata["execution_seconds"] = round(time.perf_counter()-start, 2)
    joblib.dump({"model": result.model, "metadata": result.metadata, "history": make_daily(data)}, ROOT / "artifacts/demo_model.joblib")
    (ROOT / "artifacts/demo_metadata.json").write_text(json.dumps({"metadata": result.metadata, "test_metrics": result.metrics}, indent=2))
    forecast_export(result).to_csv(ROOT / "artifacts/demo_forecast.csv", index=False)
    result.comparison.to_csv(ROOT / "artifacts/demo_model_comparison.csv", index=False)
    (ROOT / "artifacts/demo_report.md").write_text(summary_report(result))
    print(json.dumps({"rows": len(data), "selected_model": result.model_name, "seconds": result.metadata["execution_seconds"], "metrics": result.metrics}, indent=2))

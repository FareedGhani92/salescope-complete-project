from io import BytesIO
import pandas as pd
from src.reports import csv_bytes, excel_report, forecast_export, summary_report


def test_export_matches_forecast(demo_result):
    frame = forecast_export(demo_result)
    assert frame.predicted_sales.tolist() == demo_result.forecast.predicted_sales.tolist()
    assert frame.currency.eq("USD").all()
    assert "training_cutoff" in frame


def test_excel_contains_results(demo_result):
    book = pd.ExcelFile(BytesIO(excel_report(demo_result)))
    assert set(book.sheet_names) == {"Forecast", "Model comparison", "Final test", "Metadata"}
    assert len(pd.read_excel(book, "Forecast")) == 30


def test_formula_injection_is_neutralized():
    text = csv_bytes(pd.DataFrame({"product": ["=1+1"], "sales": [-20]})).decode("utf-8-sig")
    assert "'=1+1" in text and "-20" in text


def test_summary_discloses_limitations(demo_result):
    report = summary_report(demo_result)
    assert "Synthetic demo results" in report
    assert "not guaranteed" in report

from io import BytesIO
import numpy as np
import pandas as pd
import pytest
from src.data import clean_data, make_daily, read_upload, fingerprint, period_metrics


def test_cleaning_preserves_returns_and_reports_invalid():
    raw = pd.DataFrame({"when": ["2025-01-01", "bad", "2025-01-02", "2025-01-03"], "amount": [100, 30, -20, np.inf]})
    clean, q, rejected = clean_data(raw, {"date": "when", "sales": "amount"})
    assert clean.sales.sum() == 80
    assert q.invalid_rows == 2 and q.negative_sales_rows == 1
    assert len(rejected) == 2


def test_duplicates_are_opt_in():
    raw = pd.DataFrame({"date": ["2025-01-01"]*2, "sales": [10]*2})
    mapping = {"date": "date", "sales": "sales"}
    assert len(clean_data(raw, mapping)[0]) == 2
    assert len(clean_data(raw, mapping, remove_duplicates=True)[0]) == 1


def test_gaps_are_never_implicitly_zero():
    frame = pd.DataFrame({"date": pd.to_datetime(["2025-01-01", "2025-01-03"]), "sales": [10, 20]})
    with pytest.raises(ValueError, match="missing days"):
        make_daily(frame)
    assert make_daily(frame, "zero").tolist() == [10, 0, 20]


def test_mapping_rejects_reuse():
    with pytest.raises(ValueError, match="one field"):
        clean_data(pd.DataFrame({"x": [1]}), {"date": "x", "sales": "x"})


def test_all_invalid_has_actionable_error():
    with pytest.raises(ValueError, match="No valid rows"):
        clean_data(pd.DataFrame({"date": ["bad"], "sales": ["bad"]}), {"date": "date", "sales": "sales"})


def test_numeric_dates_rejected():
    with pytest.raises(ValueError, match="serials"):
        clean_data(pd.DataFrame({"date": [45240], "sales": [20]}), {"date": "date", "sales": "sales"})


def test_dayfirst_and_optional_values():
    frame = pd.DataFrame({"date": ["02/03/2025"], "sales": [10], "product": ["  "], "quantity": ["bad"]})
    clean, q, _ = clean_data(frame, {x: x for x in frame}, dayfirst=True)
    assert clean.date.iloc[0] == pd.Timestamp("2025-03-02")
    assert clean["product"].iloc[0] == "Unknown"
    assert q.quantity_invalid_rows == 1


@pytest.mark.parametrize("filename", ["test.csv", "test.xlsx"])
def test_file_roundtrip(filename):
    frame = pd.DataFrame({"date": ["2025-01-01"], "sales": [50]})
    if filename.endswith("csv"):
        content = frame.to_csv(index=False).encode()
    else:
        out = BytesIO()
        frame.to_excel(out, index=False)
        content = out.getvalue()
    assert read_upload(content, filename).sales.iloc[0] == 50


@pytest.mark.parametrize("content,name", [(b"", "x.csv"), (b"123", "x.exe"), (b"date,sales\n", "x.csv"), (b"bad", "x.xlsx")])
def test_bad_files_rejected(content, name):
    with pytest.raises(ValueError):
        read_upload(content, name)


def test_too_many_rows():
    content = b"date,sales\n" + b"2025-01-01,1\n" * 100001
    with pytest.raises(ValueError, match="100,000"):
        read_upload(content, "large.csv")


def test_order_ids_count_distinct_and_incomplete_aov_suppressed():
    frame = pd.DataFrame({"date": pd.to_datetime(["2025-01-01"]*3), "sales": [10, 20, 30], "order_id": ["A", "A", "B"]})
    assert period_metrics(frame, "2025-01-01", "2025-01-01")["aov"] == 30
    frame.loc[2, "order_id"] = None
    assert period_metrics(frame, "2025-01-01", "2025-01-01")["aov"] is None


def test_demo_reconciles(demo):
    assert len(demo) == 1096*18
    assert make_daily(demo).sum() == pytest.approx(demo.sales.sum())
    assert fingerprint(demo) != fingerprint(demo.iloc[:-1])

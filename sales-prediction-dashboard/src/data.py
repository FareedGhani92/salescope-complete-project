"""Bounded file ingestion, explicit cleaning, and daily sales aggregation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import numpy as np
import pandas as pd

MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 100_000
DIMENSIONS = ("category", "store", "product", "region")
OPTIONAL = (*DIMENSIONS, "quantity", "order_id", "promotion")


@dataclass
class Quality:
    input_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    removed_duplicates: int
    negative_sales_rows: int
    missing_dates: int
    quantity_invalid_rows: int

    def to_dict(self):
        return asdict(self)


def read_upload(content: bytes, filename: str) -> pd.DataFrame:
    if not content:
        raise ValueError("This file is empty. Choose a CSV or XLSX file with sales records.")
    if len(content) > MAX_BYTES:
        raise ValueError("Choose a file smaller than 20 MB.")
    extension = Path(filename).suffix.lower()
    try:
        if extension == ".csv":
            frame = pd.read_csv(BytesIO(content), nrows=MAX_ROWS + 1)
        elif extension == ".xlsx":
            with ZipFile(BytesIO(content)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 100 * 1024 * 1024:
                    raise ValueError("This workbook expands beyond the 100 MB processing limit.")
            frame = pd.read_excel(BytesIO(content), engine="openpyxl", nrows=MAX_ROWS + 1)
        else:
            raise ValueError("Supported formats are CSV and XLSX.")
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError, BadZipFile) as exc:
        raise ValueError("The file could not be read. Export a UTF-8 CSV or a valid XLSX workbook.") from exc
    if len(frame) > MAX_ROWS:
        raise ValueError("The limit is 100,000 rows. Upload a smaller date range or aggregate your data.")
    if frame.empty:
        raise ValueError("The file has column headers but no records.")
    frame.columns = frame.columns.astype(str).str.strip()
    if frame.columns.duplicated().any():
        raise ValueError("Column names must be unique after removing surrounding spaces.")
    return frame


def clean_data(raw: pd.DataFrame, mapping: dict[str, str], *, dayfirst=False,
               remove_duplicates=False) -> tuple[pd.DataFrame, Quality, pd.DataFrame]:
    if not {"date", "sales"}.issubset(mapping):
        raise ValueError("Map both a date column and a sales column.")
    selected = list(mapping.values())
    if len(set(selected)) != len(selected):
        raise ValueError("Each source column can only be mapped to one field.")
    if any(column not in raw.columns for column in selected):
        raise ValueError("A mapped column no longer exists. Map the file again.")
    frame = raw[selected].copy().rename(columns={v: k for k, v in mapping.items()})
    if pd.api.types.is_numeric_dtype(frame["date"]):
        raise ValueError("Dates must be text or Excel dates, not numeric serials. Export dates as YYYY-MM-DD.")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce", format="mixed",
                                    dayfirst=dayfirst, utc=True).dt.tz_convert(None).dt.normalize()
    frame["sales"] = pd.to_numeric(frame["sales"], errors="coerce")
    bad_date = frame["date"].isna()
    bad_sales = ~np.isfinite(frame["sales"].to_numpy(dtype=float, na_value=np.nan))
    invalid = bad_date | bad_sales
    rejected = raw.loc[invalid].copy()
    rejected["validation_reason"] = np.where(bad_date[invalid], "Invalid date", "Invalid or non-finite sales")
    frame = frame.loc[~invalid].copy()
    if frame.empty:
        raise ValueError("No valid rows remain. Check the date format and numeric sales values.")
    if (frame["date"].max() - frame["date"].min()).days > 7305:
        raise ValueError("The date range exceeds 20 years. Check date parsing or choose a smaller period.")
    for col in DIMENSIONS:
        if col in frame:
            frame[col] = frame[col].astype("string").str.strip().replace("", pd.NA).fillna("Unknown")
    if "order_id" in frame:
        frame["order_id"] = frame["order_id"].astype("string").str.strip().replace("", pd.NA)
    quantity_invalid = 0
    if "quantity" in frame:
        quantity = pd.to_numeric(frame["quantity"], errors="coerce")
        bad_quantity = ~np.isfinite(quantity.to_numpy(dtype=float, na_value=np.nan))
        quantity_invalid = int(bad_quantity.sum())
        frame["quantity"] = quantity.mask(bad_quantity)
    duplicate_rows = int(frame.duplicated().sum())
    if remove_duplicates:
        frame = frame.drop_duplicates()
    frame = frame.sort_values("date", kind="stable").reset_index(drop=True)
    date_count = len(pd.date_range(frame.date.min(), frame.date.max()))
    quality = Quality(len(raw), len(frame), int(invalid.sum()), duplicate_rows,
                      duplicate_rows if remove_duplicates else 0, int((frame.sales < 0).sum()),
                      date_count - frame.date.nunique(), quantity_invalid)
    return frame, quality, rejected


def make_daily(frame: pd.DataFrame, gap_policy="require") -> pd.Series:
    if frame.empty:
        raise ValueError("No sales match these filters. Broaden your selection.")
    daily = frame.groupby("date")["sales"].sum().sort_index()
    daily = daily.reindex(pd.date_range(daily.index.min(), daily.index.max(), freq="D"))
    daily.index.name = "date"
    missing = int(daily.isna().sum())
    if missing and gap_policy != "zero":
        raise ValueError(f"This selection has {missing} missing days. Confirm they represent zero sales in the sidebar, or supply complete data.")
    return daily.fillna(0).astype(float).rename("sales")


def fingerprint(frame: pd.DataFrame) -> str:
    values = pd.util.hash_pandas_object(frame, index=True).values.tobytes()
    return sha256(values + "|".join(map(str, frame.columns)).encode()).hexdigest()[:20]


def filter_data(frame, category="All", store="All", product="All"):
    result = frame
    for name, value in (("category", category), ("store", store), ("product", product)):
        if name in result and value != "All":
            result = result.loc[result[name] == value]
    return result.copy()


def period_metrics(frame: pd.DataFrame, start, end) -> dict:
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    selected = frame.loc[frame.date.between(start, end)]
    days = (end - start).days + 1
    previous_end = start - pd.Timedelta(days=1)
    previous_start = start - pd.Timedelta(days=days)
    previous = frame.loc[frame.date.between(previous_start, previous_end)]
    comparable = previous_start >= frame.date.min() and not previous.empty
    total = float(selected.sales.sum())
    previous_total = float(previous.sales.sum())
    growth = (total - previous_total) / abs(previous_total) * 100 if comparable and previous_total else None
    orders = int(selected.order_id.nunique()) if "order_id" in selected else None
    # Missing IDs make revenue-per-order incomplete, so suppress it.
    aov = total / orders if orders and selected.order_id.notna().all() else None
    return {"total": total, "daily_average": total / days, "growth": growth, "orders": orders,
            "aov": aov, "days": days, "previous_total": previous_total if comparable else None}

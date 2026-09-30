"""Deterministic synthetic retail data. Never represented as actual business results."""
from pathlib import Path
import numpy as np
import pandas as pd


def generate_demo() -> pd.DataFrame:
    rng = np.random.default_rng(2026)
    dates = pd.date_range("2023-01-01", "2025-12-31")
    products = [("Studio headphones", "Electronics", 89, 14),
                ("Portable speaker", "Electronics", 59, 20),
                ("Desk lamp", "Home & living", 39, 26),
                ("Ceramic mug set", "Home & living", 24, 36),
                ("Everyday backpack", "Lifestyle", 65, 18),
                ("Travel bottle", "Lifestyle", 29, 31)]
    frames = []
    t = np.arange(len(dates))
    for store, region, scale in [("Online", "National", 1.4), ("Central", "North", 1.0), ("Riverside", "South", .8)]:
        for product, category, price, base in products:
            weekly = np.array([.86, .90, .96, 1.02, 1.16, 1.30, 1.14])[dates.dayofweek]
            annual = 1 + .13 * np.sin(2 * np.pi * (dates.dayofyear - 240) / 365.25)
            holiday = np.where(dates.month == 11, 1.23, np.where(dates.month == 12, 1.35, 1))
            trend = 1 + .00035 * t
            promo = ((dates.day >= 12) & (dates.day <= 15)).astype(int)
            units = np.maximum(0, np.round(base * scale * weekly * annual * holiday * trend *
                              (1 + .18 * promo) + rng.normal(0, base * .11, len(dates)))).astype(int)
            revenue = np.round(units * price * (1 - .08 * promo), 2)
            frames.append(pd.DataFrame({"date": dates, "sales": revenue, "product": product,
                "category": category, "store": store, "region": region, "quantity": units, "promotion": promo}))
    return pd.concat(frames, ignore_index=True).sort_values(["date", "store", "product"]).reset_index(drop=True)


def load_demo() -> pd.DataFrame:
    path = Path(__file__).resolve().parents[1] / "data" / "sample_sales.csv"
    return pd.read_csv(path, parse_dates=["date"]) if path.exists() else generate_demo()

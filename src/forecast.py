"""Chronological model selection and genuine recursive multi-day forecasting."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import platform

import numpy as np
import pandas as pd

MODEL_NAMES = ("Seasonal baseline", "Ridge regression", "Gradient boosting")
HORIZONS = (7, 30, 90)
FEATURE_NAMES = ["lag_1", "lag_7", "lag_14", "lag_28", "mean_7", "mean_28",
                 "std_7", "weekday_sin", "weekday_cos", "year_sin", "year_cos", "trend"]


@dataclass
class ForecastResult:
    model_name: str
    comparison: pd.DataFrame
    test: pd.DataFrame
    forecast: pd.DataFrame
    metrics: dict
    metadata: dict
    model: object


def minimum_history(horizon: int) -> int:
    return 112 + 4 * horizon


def scores(actual, predicted) -> dict:
    actual, predicted = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Evaluation contains a non-finite value.")
    errors = actual - predicted
    denominator = np.abs(actual).sum()
    return {"MAE": float(np.mean(np.abs(errors))), "RMSE": float(np.sqrt(np.mean(errors ** 2))),
            "WAPE (%)": float(np.abs(errors).sum() / denominator * 100) if denominator else None}


def feature_row(history, date: pd.Timestamp, trend: int) -> list[float]:
    h = np.asarray(history[-28:], dtype=float)
    return [h[-1], h[-7], h[-14], h[-28], h[-7:].mean(), h.mean(), h[-7:].std(),
            np.sin(2 * np.pi * date.dayofweek / 7), np.cos(2 * np.pi * date.dayofweek / 7),
            np.sin(2 * np.pi * date.dayofyear / 365.25), np.cos(2 * np.pi * date.dayofyear / 365.25), trend]


def training_arrays(series: pd.Series):
    values = series.to_numpy(dtype=float)
    x = [feature_row(values[:i], date, i) for i, date in enumerate(series.index) if i >= 28]
    return np.asarray(x), values[28:]


@dataclass
class RidgeModel:
    mean: np.ndarray
    scale: np.ndarray
    coefficients: np.ndarray

    def predict(self, features):
        values = (np.asarray(features, dtype=float) - self.mean) / self.scale
        design = np.column_stack((np.ones(len(values)), values))
        return design @ self.coefficients


@dataclass
class RegressionNode:
    value: float
    feature: int = -1
    threshold: float = 0.0
    left: "RegressionNode | None" = None
    right: "RegressionNode | None" = None


@dataclass
class GradientBoostingModel:
    baseline: float
    trees: list[RegressionNode]
    learning_rate: float = .075

    def predict(self, features):
        values = np.asarray(features, dtype=float)
        result = np.full(len(values), self.baseline, dtype=float)
        for tree in self.trees:
            result += self.learning_rate * _predict_tree(tree, values)
        return result


def _fit_tree(features, targets, *, depth=0, max_depth=2, min_leaf=12,
              max_splits=16, regularization=10.0):
    count = len(targets)
    leaf_value = float(targets.sum() / (count + regularization))
    node = RegressionNode(value=leaf_value)
    if depth >= max_depth or count < 2 * min_leaf:
        return node
    total_score = float(targets.sum() ** 2 / count)
    best_gain, best_feature, best_threshold, best_mask = 0.0, -1, 0.0, None
    quantiles = np.linspace(.05, .95, max_splits)
    for feature in range(features.shape[1]):
        column = features[:, feature]
        thresholds = np.unique(np.quantile(column, quantiles))
        for threshold in thresholds:
            mask = column <= threshold
            left_count = int(mask.sum())
            right_count = count - left_count
            if left_count < min_leaf or right_count < min_leaf:
                continue
            left_sum = float(targets[mask].sum())
            right_sum = float(targets[~mask].sum())
            gain = left_sum ** 2 / left_count + right_sum ** 2 / right_count - total_score
            if gain > best_gain:
                best_gain, best_feature, best_threshold, best_mask = gain, feature, float(threshold), mask
    if best_mask is None:
        return node
    node.feature = best_feature
    node.threshold = best_threshold
    node.left = _fit_tree(features[best_mask], targets[best_mask], depth=depth + 1,
        max_depth=max_depth, min_leaf=min_leaf, max_splits=max_splits, regularization=regularization)
    node.right = _fit_tree(features[~best_mask], targets[~best_mask], depth=depth + 1,
        max_depth=max_depth, min_leaf=min_leaf, max_splits=max_splits, regularization=regularization)
    return node


def _predict_tree(node, features):
    predictions = np.empty(len(features), dtype=float)
    def fill(current, indices):
        if current.feature < 0:
            predictions[indices] = current.value
            return
        mask = features[indices, current.feature] <= current.threshold
        fill(current.left, indices[mask])
        fill(current.right, indices[~mask])
    fill(node, np.arange(len(features)))
    return predictions


def _fit_ridge(features, targets, alpha=10.0):
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale == 0] = 1.0
    normalized = (features - mean) / scale
    design = np.column_stack((np.ones(len(normalized)), normalized))
    penalty = np.eye(design.shape[1]) * alpha
    penalty[0, 0] = 0.0  # Keep an unregularized intercept, as in standard Ridge.
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ targets)
    return RidgeModel(mean, scale, coefficients)


def fit_model(name: str, series: pd.Series):
    if name == "Seasonal baseline":
        return None
    x, y = training_arrays(series)
    if name == "Ridge regression":
        return _fit_ridge(x, y, alpha=10.0)
    elif name == "Gradient boosting":
        baseline = float(y.mean())
        model = GradientBoostingModel(baseline=baseline, trees=[])
        fitted = np.full(len(y), baseline, dtype=float)
        for _ in range(40):
            tree = _fit_tree(x, y - fitted, max_depth=2, min_leaf=12,
                             max_splits=16, regularization=10.0)
            model.trees.append(tree)
            fitted += model.learning_rate * _predict_tree(tree, x)
        return model
    else:
        raise ValueError("Unknown forecasting model.")


def predict_recursive(name: str, model, history: pd.Series, horizon: int) -> np.ndarray:
    """Only the observed prefix is accepted; future actuals cannot enter lag features."""
    values = history.to_list()
    dates = pd.date_range(history.index[-1] + pd.Timedelta(days=1), periods=horizon)
    predictions = []
    for date in dates:
        if name == "Seasonal baseline":
            value = values[-7] if len(values) >= 7 else values[-1]
        else:
            value = float(model.predict(np.asarray([feature_row(values, date, len(values))]))[0])
        if not np.isfinite(value):
            raise ValueError("The model generated an invalid prediction.")
        values.append(value)
        predictions.append(value)
    return np.asarray(predictions)


def empirical_intervals(series, name, horizon):
    """Horizon-specific absolute-error bands from 20 past rolling origins.

    Origins can overlap. These are empirical ranges, not guaranteed calibrated
    probabilities under changing/nonstationary sales. The final holdout is excluded.
    """
    last_origin = len(series) - 2 * horizon
    first_origin = max(112, last_origin - max(140, 3 * horizon))
    origins = np.unique(np.linspace(first_origin, last_origin, 20, dtype=int))
    if len(origins) < 20:
        return None, 0
    errors = []
    for origin in origins:
        prefix = series.iloc[:origin]
        model = fit_model(name, prefix)
        predicted = predict_recursive(name, model, prefix, horizon)
        errors.append(np.abs(series.iloc[origin:origin+horizon].to_numpy() - predicted))
    # 'higher' avoids interpolating down from the finite-sample quantile.
    return np.quantile(np.asarray(errors), .8, axis=0, method="higher"), len(origins)


def run_forecast(series: pd.Series, horizon=30, *, currency="USD", scope="All sales",
                 data_id="", progress=None) -> ForecastResult:
    if horizon not in HORIZONS:
        raise ValueError("Choose a 7, 30, or 90 day forecast.")
    if not isinstance(series.index, pd.DatetimeIndex) or not series.index.is_unique:
        raise ValueError("Forecasting requires one record per date.")
    expected = pd.date_range(series.index.min(), series.index.max(), freq="D")
    if not series.index.equals(expected) or not np.isfinite(series.to_numpy()).all():
        raise ValueError("Forecasting requires complete, ordered daily sales.")
    if len(series) < minimum_history(horizon):
        raise ValueError(f"A {horizon}-day forecast needs at least {minimum_history(horizon)} complete days; this selection has {len(series)}.")
    def report(value, label):
        if progress:
            progress(value, label)
    rows = []
    cutoffs = [len(series) - k * horizon for k in (4, 3, 2)]
    for i, name in enumerate(MODEL_NAMES):
        report(.05 + i * .18, f"Evaluating {name.lower()} on three historical periods…")
        actuals, predictions = [], []
        try:
            for cutoff in cutoffs:
                prefix = series.iloc[:cutoff]
                model = fit_model(name, prefix)
                predicted = predict_recursive(name, model, prefix, horizon)
                actuals.extend(series.iloc[cutoff:cutoff+horizon].to_numpy())
                predictions.extend(predicted)
            rows.append({"Model": name, **scores(actuals, predictions), "Status": "Evaluated"})
        except (ValueError, FloatingPointError):
            rows.append({"Model": name, "MAE": np.nan, "RMSE": np.nan, "WAPE (%)": np.nan,
                         "Status": "Could not evaluate"})
    comparison = pd.DataFrame(rows).sort_values("MAE", kind="stable").reset_index(drop=True)
    eligible = comparison.dropna(subset=["MAE"])
    if eligible.empty:
        raise ValueError("No model could be evaluated for this selection.")
    best = eligible.iloc[0]["Model"]
    report(.62, "Checking the selected model against the untouched final period…")
    prefix = series.iloc[:-horizon]
    selected_test_model = fit_model(best, prefix)
    test_prediction = predict_recursive(best, selected_test_model, prefix, horizon)
    baseline_prediction = predict_recursive("Seasonal baseline", None, prefix, horizon)
    metrics = scores(series.iloc[-horizon:], test_prediction)
    baseline_metrics = scores(series.iloc[-horizon:], baseline_prediction)
    metrics["baseline_MAE"] = baseline_metrics["MAE"]
    metrics["improvement_pct"] = ((baseline_metrics["MAE"] - metrics["MAE"]) / baseline_metrics["MAE"] * 100
                                   if baseline_metrics["MAE"] else None)
    report(.72, "Estimating uncertainty from earlier forecast errors…")
    widths, origin_count = empirical_intervals(series, best, horizon)
    test = pd.DataFrame({"date": series.index[-horizon:], "actual": series.iloc[-horizon:].to_numpy(),
                         "predicted": test_prediction, "baseline": baseline_prediction})
    if widths is not None:
        test["lower"] = test_prediction - widths
        test["upper"] = test_prediction + widths
        metrics["coverage_pct"] = float(test.actual.between(test.lower, test.upper).mean() * 100)
        metrics["mean_band_width"] = float((2 * widths).mean())
    else:
        metrics["coverage_pct"] = None
        metrics["mean_band_width"] = None
    report(.9, "Training on all available history and generating future sales…")
    final_model = fit_model(best, series)
    prediction = predict_recursive(best, final_model, series, horizon)
    forecast = pd.DataFrame({"date": pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=horizon),
                             "predicted_sales": prediction})
    if widths is not None:
        forecast["lower_80"] = prediction - widths
        forecast["upper_80"] = prediction + widths
    metadata = {"model": best, "currency": currency, "scope": scope, "dataset_id": data_id,
                "horizon_days": horizon, "history_days": len(series),
                "training_start": str(series.index[0].date()), "training_cutoff": str(series.index[-1].date()),
                "test_start": str(test.date.min().date()), "test_end": str(test.date.max().date()),
                "validation_folds": 3, "validation_horizon_days": horizon,
                "selection_metric": "Validation MAE", "calibration_origins": origin_count,
                "interval_method": "80th percentile of absolute errors at each horizon; 20 overlapping historical origins; empirical, not guaranteed",
                "generated_at": datetime.now(timezone.utc).isoformat(), "random_seed": 2026,
                "python_version": platform.python_version(), "model_implementation": "NumPy native v1",
                "features": FEATURE_NAMES,
                "parameters": {"ridge_alpha": 10, "boosting_estimators": 40, "boosting_max_depth": 2,
                               "boosting_max_splits": 16, "boosting_learning_rate": .075,
                               "boosting_min_leaf": 12, "boosting_l2": 10}}
    report(1.0, "Forecast ready")
    return ForecastResult(best, comparison, test, forecast, metrics, metadata, final_model)

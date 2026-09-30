"""Downloads share the same values and metadata as the application."""
import json
from io import BytesIO
import pandas as pd


def safe_table(frame):
    """Neutralize spreadsheet formulas in user-supplied text, retaining numeric values."""
    result = frame.copy()
    for name in result.select_dtypes(include=["object", "string"]).columns:
        result[name] = result[name].map(lambda x: "'" + x if isinstance(x, str) and
                         x.lstrip().startswith(("=", "+", "-", "@")) else x)
    return result


def csv_bytes(frame):
    return safe_table(frame).to_csv(index=False).encode("utf-8-sig")


def forecast_export(result):
    frame = result.forecast.copy()
    for key in ("currency", "scope", "model", "training_cutoff", "horizon_days", "generated_at", "dataset_id"):
        frame[key] = result.metadata[key]
    return frame


def excel_report(result):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, frame in (("Forecast", forecast_export(result)), ("Model comparison", result.comparison),
                            ("Final test", result.test), ("Metadata", pd.DataFrame(
                                [{"setting": k, "value": str(v)} for k, v in result.metadata.items()]))):
            safe_table(frame).to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cell in sheet[1]:
                cell.font = __import__("openpyxl").styles.Font(bold=True, color="FFFFFF")
                cell.fill = __import__("openpyxl").styles.PatternFill("solid", fgColor="172B4D")
                sheet.column_dimensions[cell.column_letter].width = 24
    return output.getvalue()


def summary_report(result):
    m, meta = result.metrics, result.metadata
    return f"""# Salescope forecast report

- Scope: {meta['scope']}
- Currency: {meta['currency']}
- Model: {meta['model']}
- History: {meta['training_start']} to {meta['training_cutoff']}
- Forecast horizon: {meta['horizon_days']} days
- Forecast total: {result.forecast.predicted_sales.sum():,.2f} {meta['currency']}
- Final test: {meta['test_start']} to {meta['test_end']}
- Final test MAE: {m['MAE']:,.2f} {meta['currency']}
- Final test RMSE: {m['RMSE']:,.2f} {meta['currency']}
- Final test WAPE (%): {m['WAPE (%)']}
- Seasonal baseline test MAE: {m['baseline_MAE']:,.2f}
- Empirical range coverage on final test (%): {m['coverage_pct']}
- Generated: {meta['generated_at']}

## Method and limitations

Models are selected by mean MAE over three earlier chronological forecast windows.
The selected model is evaluated on the final held-out period, then refitted on all
available history. Recursive forecasts never consume actual sales inside a forecast window.
Ranges use horizon-specific errors from 20 earlier, potentially overlapping origins.
They are empirical uncertainty estimates, not guaranteed probabilities. Individual
daily bounds must not be added together as a confidence interval for the total.
Sales may be negative when modeling net revenue with returns. Forecasts do not
model future promotions, prices, stockouts, or external shocks explicitly.
Synthetic demo results do not establish real-world accuracy.

## Reproduction metadata

```json
{json.dumps(meta, indent=2)}
```
"""

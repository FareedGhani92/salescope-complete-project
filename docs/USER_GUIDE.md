# Salescope user guide

## Open the app

The app starts with a synthetic retail dataset. Its records cover 2023–2025, six products, and three stores. Currency defaults to USD. You can explore the complete app without uploading anything.

## Overview and analysis

Choose a category, store, or product in the sidebar. The analysis period initially covers the latest 90 days. The revenue total includes only the selected records and dates. Average daily sales excludes unknown missing dates, unless you explicitly confirm they mean zero sales. Growth is suppressed when there is no complete, non-zero previous period.

Overview displays a daily trend and seven-day average. Sales analysis adds daily/weekly/monthly views and weekday and business-dimension comparisons. Weekly and monthly boundary periods may be incomplete. Use “Explore the records” to inspect and download the filtered input.

## Upload your data

1. Open Data workspace → Upload your data.
2. Select CSV or XLSX. For XLSX, only the first worksheet is read.
3. Map date and sales, then any optional fields.
4. Select the row meaning and date convention.
5. Inspect invalid rows, duplicate candidates, missing dates, and returns.
6. Download rejected rows if you need to repair them. Explicitly confirm their exclusion to continue.
7. Remove exact duplicates only if they are accidental copies.
8. Click “Use this dataset.” The sidebar will show its name and range.
9. Set the correct currency label; this does not convert the numbers.

Uploads replace the active session dataset. The sample can be restored at any time. Invalid optional quantity values are omitted from quantity totals while their valid sales values remain.

## Generate a forecast

1. Select the business segment in the sidebar.
2. Open Forecast studio.
3. Choose 7, 30, or 90 days.
4. Resolve missing dates or explicitly confirm zero sales.
5. Click Generate forecast.

Forecasts begin after the last available date. All available history for the selected segment is used; the analysis page's chart dates do not shorten model training.

The app compares three models on earlier periods, chooses the best validation MAE, measures its final test error, and refits it on all history. It may choose the seasonal baseline. No model is guaranteed to outperform the baseline on every later period.

## Interpret the output

The line separates recorded sales from predictions. The shaded range targets 80% empirical coverage but can under-cover when the business changes. Read the actual final-test coverage shown below the chart. Do not add daily lower/upper bounds to form a range for the period total.

MAE and RMSE are expressed in currency units. WAPE is a percentage error and is unavailable for an all-zero denominator. The dashboard does not report classification-style “accuracy.” Negative forecast values are possible because sales is treated as net revenue, including returns.

## Export

Forecast studio provides a CSV with prediction and reproduction metadata. Reports & guide also provides a formatted Excel workbook, a Markdown summary, and the model comparison. Data workspace exports validated records and the cleaning summary.

Changing the dataset, currency, selected segment, missing-days policy, or forecast horizon invalidates the current result for that selection. Return to Forecast studio and generate a new forecast. Download anything you want to keep before leaving or restarting the application.

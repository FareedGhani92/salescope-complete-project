"""Salescope — Streamlit portfolio application. Run: streamlit run app.py"""
from __future__ import annotations

import html
import json
from datetime import timedelta
from hashlib import sha256

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import PALETTE, bars, forecast_chart, revenue_chart, style, test_chart
from src.data import OPTIONAL, clean_data, filter_data, fingerprint, make_daily, period_metrics, read_upload
from src.demo import load_demo
from src.forecast import HORIZONS, minimum_history, run_forecast
from src.reports import csv_bytes, excel_report, forecast_export, summary_report

st.set_page_config(page_title="Salescope · Sales intelligence", page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded", menu_items={"About": "Salescope — sales analytics and time-aware forecasting. Synthetic demo data is clearly labeled."})

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp {font-family:'DM Sans',sans-serif;}
h1,h2,h3 {font-family:'Manrope',sans-serif;letter-spacing:-.035em;color:#172B4D;}
h1 {font-size:2.15rem!important;font-weight:800!important;padding-bottom:.35rem!important;}
h2 {font-size:1.35rem!important;} h3 {font-size:1.05rem!important;}
.block-container {padding-top:2.3rem;max-width:1480px;padding-bottom:3rem;}
[data-testid="stHeader"] {background:rgba(246,248,252,.88);}
[data-testid="stSidebar"] {background:#111E35;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] .stCaption {color:#E2E9F5!important;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#A8B6CD!important;font-size:.8rem!important;}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding:7px 4px;}
[data-testid="stSidebar"] [data-testid="stRadio"] label p {font-size:.94rem;}
[data-testid="stSidebar"] hr {border-color:#304059;}
[data-testid="stSidebar"] .stButton button {background:#20324C;border-color:#40516B;color:#E2E9F5;}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {background:#20324C;border-radius:8px;}
[data-testid="stMetric"] {background:white;border:1px solid #E3E9F2;border-radius:12px;padding:20px 22px;}
[data-testid="stMetricLabel"] {color:#697991;font-size:.83rem;}
[data-testid="stMetricValue"] {font-family:'Manrope',sans-serif;font-size:1.9rem;font-weight:800;letter-spacing:-.04em;}
[data-testid="stVerticalBlockBorderWrapper"]>div {border-radius:14px;}
.stButton>button,.stDownloadButton>button {border-radius:8px;font-weight:600;}
.brand {font-family:'Manrope',sans-serif;font-weight:800;font-size:1.7rem;color:white;letter-spacing:-.06em;}
.brand-mark {display:inline-flex;align-items:center;justify-content:center;width:35px;height:35px;background:#13AFAD;border-radius:9px;color:#fff;margin-right:8px;font-size:1.3rem;}
.eyebrow {color:#697991;font-weight:700;font-size:.75rem;letter-spacing:.13em;text-transform:uppercase;margin-bottom:5px;}
.subtle {color:#697991;font-size:.95rem;line-height:1.6;margin-bottom:22px;}
.pill {display:inline-block;background:#E5F4F2;color:#07676B;border:1px solid #CBE5E2;border-radius:100px;padding:5px 11px;font-size:.75rem;font-weight:600;}
.insight {border-left:3px solid #087F8C;padding:4px 0 4px 15px;margin:14px 0;color:#435570;line-height:1.6;font-size:.92rem;}
.footer {color:#8190A5;font-size:.78rem;border-top:1px solid #E0E7F0;padding-top:18px;margin-top:30px;}
@media(max-width:1100px){
 [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]){flex-wrap:wrap;}
 [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])>[data-testid="stColumn"]{flex:1 1 180px!important;min-width:180px!important;}
 [data-testid="stMetric"]{padding:16px;}
 [data-testid="stMetricValue"]{font-size:1.5rem!important;}
}
@media(max-width:700px){.block-container{padding:1rem;}h1{font-size:1.7rem!important;}[data-testid="stMetricValue"]{font-size:1.5rem;}}
</style>""", unsafe_allow_html=True)


def escaped(value):
    return html.escape(str(value))


def money(value, compact=False):
    if value is None or not np.isfinite(value):
        return "—"
    if compact and abs(value) >= 1_000_000:
        return f"{currency} {value/1_000_000:,.2f}M"
    if compact and abs(value) >= 1000:
        return f"{currency} {value/1000:,.1f}K"
    return f"{currency} {value:,.0f}"


def heading(title, subtitle, eyebrow="SALES INTELLIGENCE"):
    st.markdown(f'<div class="eyebrow">{escaped(eyebrow)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="subtle">{escaped(subtitle)}</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def demo_dataset():
    raw = load_demo()
    frame, quality, _ = clean_data(raw, {col: col for col in raw.columns})
    return frame, quality


def activate_demo():
    frame, quality = demo_dataset()
    st.session_state.dataset = frame
    st.session_state.quality = quality
    st.session_state.source = "Synthetic retail demo"
    st.session_state.grain = "Daily totals by product and store"
    st.session_state.currency = "USD"
    st.session_state.dataset_id = fingerprint(frame)
    st.session_state.pop("forecast_result", None)
    st.session_state.pop("forecast_signature", None)
    st.session_state.rejected = pd.DataFrame()


def restore_demo():
    activate_demo()
    for key in list(st.session_state):
        if key.endswith(("_category", "_store", "_product")):
            del st.session_state[key]


if "dataset" not in st.session_state:
    activate_demo()

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">↗</span>salescope</div>', unsafe_allow_html=True)
    st.caption("SALES ANALYTICS & FORECASTING")
    st.write("")
    page = st.radio("Workspace", ["Overview", "Sales analysis", "Forecast studio", "Model performance", "Data workspace", "Reports & guide"], label_visibility="collapsed", key="navigation")
    st.divider()
    st.markdown("**CURRENT DATASET**")
    st.caption(st.session_state.source)
    frame = st.session_state.dataset
    dataset_id = st.session_state.dataset_id
    st.caption(f"{len(frame):,} records · {frame.date.min():%d %b %Y} – {frame.date.max():%d %b %Y}")
    currency = st.selectbox("Currency label", ["USD", "PKR", "EUR", "GBP", "INR", "AED", "CAD", "AUD"], key="currency",
                            help="Changes labels only. No currency conversion is performed.")
    selections = {}
    for dimension in ("category", "store", "product"):
        if dimension in frame:
            options = [None] + sorted(frame[dimension].dropna().unique().tolist())
            selections[dimension] = st.selectbox(dimension.title(), options,
                format_func=lambda x: "All" if x is None else x, key=f"{dataset_id}_{dimension}")
    selected_frame = frame.copy()
    for dimension, value in selections.items():
        if value is not None:
            selected_frame = selected_frame.loc[selected_frame[dimension] == value]
    scope = " · ".join(f"{k.title()}: {v}" for k, v in selections.items() if v is not None) or "All sales"
    missing_zero = st.checkbox("Missing days mean zero sales", key=f"zero_{dataset_id}",
        help="Enable only when absent dates truly had no sales. This applies to the selected segment.")
    st.caption("Forecasts use all history for this selection. Chart dates are controlled on each analysis page.")
    st.divider()
    st.button("Restore sample dataset", width="stretch", on_click=restore_demo)
    st.caption("Built with Streamlit · No API key needed")

st.markdown(f'<span class="pill">{escaped(st.session_state.source)} · {escaped(currency)}</span>', unsafe_allow_html=True)
st.write("")


def daily_for_forecast():
    try:
        return make_daily(selected_frame, "zero" if missing_zero else "require")
    except ValueError as exc:
        st.info(str(exc))
        return None


def signature(horizon):
    return json.dumps({"dataset": dataset_id, "selection": selections, "currency": currency,
                       "horizon": horizon, "zero_missing": missing_zero}, sort_keys=True)


def current_result():
    result = st.session_state.get("forecast_result")
    if result is not None and st.session_state.get("forecast_signature") == signature(st.session_state.get("forecast_config_horizon", 30)):
        return result
    return None


def forecast_controls():
    daily = daily_for_forecast()
    if daily is None:
        return None, None
    c1, c2 = st.columns([1, 2])
    with c1:
        horizon = st.selectbox("Forecast horizon", HORIZONS, index=HORIZONS.index(st.session_state.get("forecast_config_horizon", 30)), format_func=lambda n: f"Next {n} days", key="horizon")
        st.session_state.forecast_config_horizon = horizon
    with c2:
        st.caption(f"Training history: {daily.index[0]:%d %b %Y} – {daily.index[-1]:%d %b %Y} · {len(daily):,} days")
        st.caption("The forecast begins after the last recorded sale, not today's date.")
    eligible = len(daily) >= minimum_history(horizon)
    if not eligible:
        st.warning(f"This horizon needs {minimum_history(horizon)} complete days. There are {len(daily)}. Try a shorter horizon or broader selection.")
    if st.button("Generate forecast", type="primary", disabled=not eligible, icon=":material/auto_awesome:"):
        progress = st.progress(0, text="Preparing historical evaluation…")
        try:
            result = run_forecast(daily, horizon, currency=currency, scope=scope, data_id=dataset_id,
                progress=lambda value, label: progress.progress(value, text=label))
            result.metadata["data_source"] = st.session_state.source
            result.metadata["row_grain"] = st.session_state.grain
            result.metadata["missing_days_policy"] = "Confirmed zero sales" if missing_zero else "Require complete dates"
            st.session_state.forecast_result = result
            st.session_state.forecast_signature = signature(horizon)
        except (ValueError, ArithmeticError) as exc:
            st.error(f"Unable to forecast this selection: {exc}")
        finally:
            progress.empty()
    return daily, current_result()


def date_selection(data):
    end = data.date.max().date()
    start = max(data.date.min().date(), end - timedelta(days=89))
    key = f"dates_{dataset_id}_{scope}_{page}"
    selected = st.date_input("Analysis period", value=(start, end), min_value=data.date.min().date(),
                             max_value=end, key=key, format="DD/MM/YYYY")
    if len(selected) != 2:
        st.info("Choose both a start date and an end date.")
        st.stop()
    return selected


def observed_daily(data, start, end):
    daily = data.groupby("date").sales.sum().reindex(pd.date_range(start, end))
    if missing_zero:
        daily = daily.fillna(0)
    if daily.isna().any():
        st.caption(f"{daily.isna().sum()} missing dates are shown as gaps. Confirm zero-sales days in the sidebar only if appropriate.")
    return daily


if page in ("Overview", "Sales analysis"):
    heading("Your sales, in perspective." if page == "Overview" else "Find the patterns behind sales.",
        "Explore performance, spot changes, and plan your next move." if page == "Overview" else "Compare time periods, products, and the rhythm of your business.",
        "OVERVIEW" if page == "Overview" else "SALES ANALYSIS")
    if selected_frame.empty:
        st.info("No records match this combination. Broaden the sidebar filters.")
        st.stop()
    period_col, scope_col = st.columns([1, 2])
    with period_col:
        start, end = date_selection(selected_frame)
    with scope_col:
        st.caption(f"Scope: {scope}")
        st.caption("Growth compares the previous period of equal length when available.")
    visible = selected_frame.loc[selected_frame.date.between(pd.Timestamp(start), pd.Timestamp(end))]
    if visible.empty:
        st.info("No sales records fall inside this period.")
        st.stop()
    metrics = period_metrics(selected_frame, start, end)
    daily = observed_daily(visible, start, end)
    previous_start = pd.Timestamp(start) - pd.Timedelta(days=metrics["days"])
    previous_dates = selected_frame.loc[selected_frame.date.between(previous_start, pd.Timestamp(start)-pd.Timedelta(days=1)), "date"].nunique()
    complete_comparison = (missing_zero or (daily.notna().all() and previous_dates == metrics["days"]))
    growth = metrics["growth"] if complete_comparison else None
    cards = st.columns(4)
    cards[0].metric("TOTAL SALES", money(metrics["total"], True), f"{growth:+.1f}% vs previous period" if growth is not None else None)
    cards[1].metric("AVERAGE DAILY SALES", money(float(daily.mean()), True), help="Average across observed days, or all days when missing dates are confirmed zero.")
    cards[2].metric("BEST SALES DAY", money(float(daily.max()), True), f"{daily.idxmax():%a, %d %b}", delta_color="off")
    if metrics["aov"] is not None:
        cards[3].metric("AVERAGE ORDER VALUE", money(metrics["aov"]), f"{metrics['orders']:,} distinct orders", delta_color="off")
    elif "quantity" in visible:
        cards[3].metric("UNITS SOLD", f"{visible.quantity.sum():,.0f}", "Based on available quantity records", delta_color="off")
    else:
        cards[3].metric("DAYS WITH RECORDS", f"{visible.date.nunique():,}", f"of {metrics['days']} calendar days", delta_color="off")
    st.write("")
    with st.container(border=True):
        st.subheader("Revenue over time")
        st.caption(f"{start:%d %b %Y} – {end:%d %b %Y} · {currency}")
        if page == "Sales analysis":
            granularity = st.segmented_control("View", ["Daily", "Weekly", "Monthly"], default="Daily")
            if granularity in ("Weekly", "Monthly"):
                daily_view = daily.resample("W-MON" if granularity == "Weekly" else "MS").sum(min_count=1)
                fig = px.bar(x=daily_view.index, y=daily_view.values, color_discrete_sequence=["#087F8C"])
                st.plotly_chart(style(fig), width="stretch")
                st.caption("Weekly and monthly bars include partial periods at the selected date boundaries.")
            else:
                st.plotly_chart(revenue_chart(daily, currency), width="stretch")
        else:
            st.plotly_chart(revenue_chart(daily, currency), width="stretch")
    left, right = st.columns([1.3, 1])
    dimension = "product" if "product" in visible else "category" if "category" in visible else None
    with left, st.container(border=True):
        st.subheader("Top performers" if dimension else "Sales by weekday")
        if dimension:
            grouped = visible.groupby(dimension, as_index=False).sales.sum().nlargest(6, "sales")
            st.caption(f"Top {len(grouped)} {dimension}s by revenue")
            st.plotly_chart(bars(grouped, dimension), width="stretch")
        else:
            by_day = daily.groupby(daily.index.day_name()).mean().reset_index()
            by_day.columns = ["weekday", "sales"]
            st.plotly_chart(bars(by_day, "weekday"), width="stretch")
    with right, st.container(border=True):
        st.subheader("At a glance")
        weekday = daily.groupby(daily.index.day_name()).mean().dropna()
        observations = [f"{weekday.idxmax()} has the highest average daily sales in this period: {money(weekday.max())}."]
        if "category" in visible:
            totals = visible.groupby("category").sales.sum().sort_values(ascending=False)
            observations.append(f"{totals.index[0]} leads category revenue with {money(totals.iloc[0], True)}.")
        if growth is not None:
            observations.append(f"Revenue is {'up' if growth >= 0 else 'down'} {abs(growth):.1f}% against the previous {metrics['days']}-day period.")
        else:
            observations.append("A complete, non-zero previous period is needed for a reliable growth comparison.")
        for text in observations:
            st.markdown(f'<div class="insight">{escaped(text)}</div>', unsafe_allow_html=True)
        st.caption("Calculated from historical records in the selected period.")
    if page == "Sales analysis":
        a, b = st.columns(2)
        with a, st.container(border=True):
            st.subheader("Weekly rhythm")
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            by_day = daily.groupby(daily.index.day_name()).mean().reindex(weekdays)
            fig = px.bar(x=[d[:3] for d in weekdays], y=by_day.values, color_discrete_sequence=["#7664DF"])
            st.plotly_chart(style(fig, 300), width="stretch")
            st.caption("Average daily sales by weekday.")
        with b, st.container(border=True):
            dim = next((d for d in ("store", "category", "region") if d in visible), None)
            st.subheader(f"Sales by {dim}" if dim else "Distribution of daily sales")
            if dim:
                st.plotly_chart(bars(visible.groupby(dim, as_index=False).sales.sum(), dim), width="stretch")
            else:
                st.plotly_chart(style(px.histogram(x=daily.dropna(), nbins=20, color_discrete_sequence=["#087F8C"]), 300), width="stretch")
    with st.expander("Explore the records"):
        st.dataframe(visible, hide_index=True, width="stretch")
        st.download_button("Download filtered sales", csv_bytes(visible), "filtered_sales.csv", "text/csv")

elif page == "Forecast studio":
    heading("A clearer view of what's next.", "Compare three forecasting approaches, then project sales beyond your latest record.", "FORECAST STUDIO")
    with st.container(border=True):
        st.subheader("Build your forecast")
        st.caption(f"Scope: {scope} · Models are selected using earlier historical periods.")
        daily, result = forecast_controls()
    if result is not None:
        f = result.forecast
        a, b, c = st.columns(3)
        a.metric("PREDICTED PERIOD SALES", money(float(f.predicted_sales.sum()), True))
        b.metric("EXPECTED DAILY AVERAGE", money(float(f.predicted_sales.mean()), True))
        c.metric("HISTORICAL TEST ERROR · MAE", money(result.metrics["MAE"], True))
        with st.container(border=True):
            st.subheader("From history to possibility")
            st.caption(f"{result.model_name} · {f.date.min():%d %b} – {f.date.max():%d %b %Y}")
            st.plotly_chart(forecast_chart(daily, result), width="stretch")
            st.caption("The shaded area is an empirical 80% prediction range. It is an estimate, not a guarantee; daily bounds cannot be summed into a range for the total.")
        if result.metrics["coverage_pct"] is not None:
            st.info(f"On the final historical test, {result.metrics['coverage_pct']:.0f}% of actual days fell inside the estimated 80% range. Longer forecasts and changing sales patterns can increase error.")
        else:
            st.info("There is too little calibration history to display a reliable uncertainty range.")
        with st.expander("Forecast values", expanded=True):
            st.dataframe(f, hide_index=True, width="stretch", column_config={"date": st.column_config.DateColumn("Date"),
                "predicted_sales": st.column_config.NumberColumn(f"Predicted sales ({currency})", format="%.2f"),
                "lower_80": st.column_config.NumberColumn("Lower estimate", format="%.2f"),
                "upper_80": st.column_config.NumberColumn("Upper estimate", format="%.2f")})
        st.download_button("Download forecast CSV", csv_bytes(forecast_export(result)), "salescope_forecast.csv", "text/csv", type="primary")
    else:
        st.info("Choose a horizon and generate a forecast. Predictions and evaluation results will appear here.")
        st.caption("Three chronological validation windows · An untouched final test · Refit on all available history")

elif page == "Model performance":
    heading("Understand the forecast, not just the number.", "Compare models on earlier periods, then inspect the selected model on its final historical test.", "MODEL PERFORMANCE")
    result = current_result()
    if result is None:
        st.info("Generate a forecast in Forecast studio for the current dataset and filters to see its performance.")
        with st.expander("What gets compared?", expanded=True):
            st.write("**Seasonal baseline:** repeats the previous matching weekday. **Ridge regression:** learns a regularized relationship between calendar and past-sales features. **Gradient boosting:** learns nonlinear patterns. Lowest validation MAE wins, even when the baseline is best.")
    else:
        m = result.metrics
        cols = st.columns(4)
        cols[0].metric("TEST MAE", money(m["MAE"], True))
        cols[1].metric("TEST RMSE", money(m["RMSE"], True))
        cols[2].metric("TEST WAPE", f"{m['WAPE (%)']:.1f}%" if m['WAPE (%)'] is not None else "Not available")
        cols[3].metric("MAE IMPROVEMENT VS BASELINE", f"{m['improvement_pct']:+.1f}%" if m['improvement_pct'] is not None else "Not available")
        with st.container(border=True):
            st.subheader("Model leaderboard")
            st.caption("Selection uses three earlier validation windows. These scores are separate from the final test metrics above.")
            st.dataframe(result.comparison, hide_index=True, width="stretch",
                column_config={name: st.column_config.NumberColumn(name, format="%.2f") for name in ("MAE", "RMSE", "WAPE (%)")})
            st.success(f"Selected: {result.model_name}")
        with st.container(border=True):
            st.subheader("The final reality check")
            st.caption(f"Untouched test period: {result.metadata['test_start']} – {result.metadata['test_end']}")
            st.plotly_chart(test_chart(result.test), width="stretch")
        st.caption("Positive improvement means lower test MAE than the baseline. Negative improvement means the baseline did better on this final period; model selection is not revised using test outcomes.")
        with st.expander("Reproduction details"):
            st.json(result.metadata)

elif page == "Data workspace":
    heading("Good forecasts start with good data.", "Inspect the sample dataset or bring your own sales history. CSV and XLSX files up to 20 MB are supported.", "DATA WORKSPACE")
    tab_upload, tab_current = st.tabs(["Upload your data", "Current dataset"])
    with tab_upload:
        st.caption("Required: a date column and numeric sales revenue. XLSX imports the first worksheet. Use one currency per dataset.")
        uploaded = st.file_uploader("Choose a sales file", type=["csv", "xlsx"])
        if uploaded is not None:
            try:
                content = uploaded.getvalue()
                upload_id = sha256(content).hexdigest()[:12]
                raw = read_upload(content, uploaded.name)
                st.caption(f"{len(raw):,} rows · {len(raw.columns)} columns")
                st.dataframe(raw.head(8), hide_index=True, width="stretch")
                mapping = {}
                left, right = st.columns(2)
                for field, col in (("date", left), ("sales", right)):
                    names = list(raw.columns)
                    guesses = [i for i, name in enumerate(names) if name.lower() in ({"date", "order_date", "order date", "sales_date"} if field == "date" else {"sales", "revenue", "net_sales", "amount"})]
                    mapping[field] = col.selectbox(f"{field.title()} column", names, index=guesses[0] if guesses else 0, key=f"map_{upload_id}_{field}")
                with st.expander("Optional columns", expanded=True):
                    pairs = st.columns(2)
                    for i, field in enumerate(OPTIONAL):
                        options = [None] + list(raw.columns)
                        default = next((i for i, name in enumerate(options) if name and name.lower() == field), 0)
                        chosen = pairs[i % 2].selectbox(field.replace("_", " ").title(), options, index=default,
                            format_func=lambda x: "Not provided" if x is None else x, key=f"map_{upload_id}_{field}")
                        if chosen is not None:
                            mapping[field] = chosen
                grain = st.selectbox("Each row represents", ["A daily total", "An order line", "A transaction"], key=f"grain_{upload_id}")
                st.caption("Order IDs must identify orders uniquely across the dataset. Sales must be numeric, without currency symbols or thousands separators.")
                dayfirst = st.checkbox("Dates use day/month/year", key=f"dayfirst_{upload_id}")
                remove_duplicates = st.checkbox("Remove exact duplicate mapped rows", key=f"dedup_{upload_id}", help="Leave off if identical-looking rows are legitimate separate sales.")
                clean, quality, rejected = clean_data(raw, mapping, dayfirst=dayfirst, remove_duplicates=remove_duplicates)
                a, b, c = st.columns(3)
                a.metric("VALID ROWS", f"{quality.valid_rows:,}")
                b.metric("INVALID ROWS", f"{quality.invalid_rows:,}")
                c.metric("DUPLICATE CANDIDATES", f"{quality.duplicate_rows:,}")
                if quality.quantity_invalid_rows:
                    st.warning(f"{quality.quantity_invalid_rows} quantity values are unavailable. Their sales records are retained.")
                st.caption(f"Valid date range: {clean.date.min():%d %b %Y} – {clean.date.max():%d %b %Y}. Negative revenue rows: {quality.negative_sales_rows:,}. Missing dates: {quality.missing_dates:,}.")
                acknowledged = True
                if len(rejected):
                    st.dataframe(rejected.head(20), hide_index=True)
                    st.download_button("Download invalid rows", csv_bytes(rejected), "invalid_rows.csv", "text/csv")
                    acknowledged = st.checkbox("Exclude the invalid rows listed above", key=f"exclude_{upload_id}")
                if st.button("Use this dataset", type="primary", disabled=not acknowledged):
                    st.session_state.dataset = clean
                    st.session_state.quality = quality
                    st.session_state.rejected = rejected
                    st.session_state.source = uploaded.name
                    st.session_state.grain = grain
                    st.session_state.dataset_id = fingerprint(clean)
                    st.session_state.pop("forecast_result", None)
                    st.session_state.pop("forecast_signature", None)
                    st.rerun()
            except (ValueError, KeyError, TypeError, OSError) as exc:
                st.error(str(exc))
        st.download_button("Download sample CSV", csv_bytes(demo_dataset()[0]), "sample_sales.csv", "text/csv")
        st.caption("Uploads are held in the server session's memory. They are not intentionally written to disk. Download results before your session ends.")
    with tab_current:
        q = st.session_state.quality
        st.write(f"**{st.session_state.source}** · {st.session_state.grain}")
        st.json(q.to_dict(), expanded=True)
        st.dataframe(frame.head(200), hide_index=True, width="stretch")
        st.caption("Preview shows the first 200 records. Downloads contain all validated records.")
        st.download_button("Download validated data", csv_bytes(frame), "validated_sales.csv", "text/csv")
        st.download_button("Download cleaning summary", json.dumps(q.to_dict(), indent=2), "cleaning_summary.json", "application/json")

elif page == "Reports & guide":
    heading("Take the insight with you.", "Export your work, understand the methodology, and make the dashboard your own.", "REPORTS & GUIDE")
    result = current_result()
    if result is not None:
        with st.container(border=True):
            st.subheader("Your latest forecast")
            st.caption(f"{result.model_name} · {result.metadata['scope']} · {result.metadata['horizon_days']} days")
            a, b, c = st.columns(3)
            a.download_button("Forecast CSV", csv_bytes(forecast_export(result)), "salescope_forecast.csv", "text/csv", width="stretch")
            b.download_button("Excel report", excel_report(result), "salescope_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
            c.download_button("Summary report", summary_report(result), "salescope_report.md", "text/markdown", width="stretch")
            st.download_button("Model comparison CSV", csv_bytes(result.comparison), "model_comparison.csv", "text/csv")
    else:
        st.info("Generate a forecast for the current selection to unlock forecast reports.")
    with st.expander("Start here", expanded=True):
        st.markdown("1. Explore the synthetic sample data on **Overview**.\n2. To use your own data, open **Data workspace**, map your columns, and review the validation summary.\n3. Choose a category, store, or product in the sidebar.\n4. Open **Forecast studio**, select a horizon, and generate a forecast.\n5. Review **Model performance** before using a prediction.\n6. Download results here or from the relevant page.")
    with st.expander("What the numbers mean"):
        st.markdown("**MAE:** average absolute daily error, in your selected currency. Lower is better.\n\n**RMSE:** gives larger errors more weight.\n\n**WAPE:** total absolute error divided by total absolute actual sales. Unavailable when the denominator is zero.\n\n**Growth:** change from the previous equal-length period, divided by the absolute previous total.\n\n**Prediction range:** historical uncertainty at each forecast horizon. Its target is 80%, but observed coverage can differ.\n\n**Currency:** a display label. The app does not convert currencies.")
    with st.expander("How forecasting works"):
        st.write("The application compares a weekly seasonal baseline, Ridge regression, and gradient boosting. Models use calendar signals, lagged sales, and shifted rolling statistics. Three chronological validation windows determine the winner. The final period is held out for evaluation. Multi-day forecasts recursively use predicted values for unavailable future lags. The final model is then refitted on all observed history.")
        st.write("Uncertainty is estimated from 20 earlier forecast origins at matching horizons. These origins may overlap; the bands are empirical estimates, not guaranteed confidence levels. Daily limits are not valid limits for the forecast total.")
    with st.expander("Data requirements and limitations"):
        st.write("Upload UTF-8 CSV or XLSX (first sheet), up to 20 MB and 100,000 rows. Date and sales are required. At least 140, 232, or 472 complete days are needed for a 7-, 30-, or 90-day forecast. Missing days must be resolved or explicitly confirmed as zero sales. Numeric Excel date serials are not supported; export calendar dates instead.")
        st.write("The demo uses synthetic USD retail data from 2023–2025. Its results are illustrative. Models do not explicitly account for future promotions, price changes, inventory shortages, or market shocks. Negative predictions and ranges are possible because net revenue can include returns. Each selected segment is modeled independently; forecasts are not reconciled across products or stores.")
        st.write("No external AI service receives uploaded data. Uploads live in server session memory and are cleared with session disposal or replacement. Public demo access has no application-level authentication; use synthetic or non-sensitive data. Hosting must be configured appropriately before accepting confidential business records.")
    with st.expander("Portfolio and deployment"):
        st.write("This project includes a README, deployment guide, model card, tests, Dockerfile, and CI workflow. Streamlit Community Cloud can run app.py directly from your GitHub repository. No API keys are required.")
        st.link_button("Streamlit deployment documentation", "https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app")

st.markdown('<div class="footer">Salescope · Thoughtful forecasts start with honest data. &nbsp; Built with Python, Streamlit & NumPy.</div>', unsafe_allow_html=True)

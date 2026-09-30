"""Consistent, readable interactive charts."""
import plotly.express as px
import plotly.graph_objects as go

TEAL = "#087F8C"
NAVY = "#172B4D"
PURPLE = "#7664DF"
PALETTE = [TEAL, PURPLE, "#479AD1", "#E7A84B", "#6B7C99", "#D36D87"]


def style(fig, height=350):
    fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=13, color=NAVY),
        margin=dict(l=8, r=16, t=20, b=12), hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, title=None),
        xaxis_title=None, yaxis_title=None)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#E6EBF3", zeroline=False, tickformat="~s")
    return fig


def revenue_chart(daily, currency):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily.index, y=daily.values, name="Daily sales", mode="lines",
        line=dict(color=TEAL, width=2.5), fill="tozeroy", fillcolor="rgba(8,127,140,.07)"))
    fig.add_trace(go.Scatter(x=daily.index, y=daily.rolling(7, min_periods=7).mean(), name="7-day average",
        line=dict(color=PURPLE, width=2, dash="dot")))
    fig.update_layout(yaxis_ticksuffix=f" {currency}")
    return style(fig)


def bars(frame, dimension, value="sales", horizontal=True):
    ordered = frame.sort_values(value, ascending=horizontal)
    fig = px.bar(ordered, x=value if horizontal else dimension, y=dimension if horizontal else value,
        orientation="h" if horizontal else "v", color_discrete_sequence=[TEAL])
    fig.update_traces(marker_line_width=0, marker_cornerradius=5)
    fig.update_layout(bargap=.35)
    return style(fig, max(270, min(420, 55 * len(ordered))))


def forecast_chart(history, result):
    fig = go.Figure()
    history = history.iloc[-120:]
    future = result.forecast
    fig.add_trace(go.Scatter(x=history.index, y=history, name="Observed sales", line=dict(color=TEAL, width=2)))
    if "lower_80" in future:
        fig.add_trace(go.Scatter(x=future.date, y=future.upper_80, line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=future.date, y=future.lower_80, fill="tonexty", fillcolor="rgba(118,100,223,.15)",
            line=dict(width=0), name="Empirical 80% range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=future.date, y=future.predicted_sales, name="Forecast",
        line=dict(color=PURPLE, width=2.5, dash="dash")))
    fig.add_vline(x=history.index[-1].timestamp()*1000, line_color="#ABB7CB", line_dash="dot")
    return style(fig, 400)


def test_chart(test):
    fig = go.Figure()
    for column, label, color, dash in [("actual", "Actual sales", TEAL, None),
        ("predicted", "Selected model", PURPLE, "dash"), ("baseline", "Seasonal baseline", "#9AA6BA", "dot")]:
        fig.add_trace(go.Scatter(x=test.date, y=test[column], name=label, line=dict(color=color, dash=dash, width=2)))
    return style(fig, 360)

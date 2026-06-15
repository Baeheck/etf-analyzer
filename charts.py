import plotly.graph_objects as go
import pandas as pd


def normalized_performance_chart(prices: pd.DataFrame) -> go.Figure:
    """
    Normalizes each ETF to 100 at its first available date.
    Lets you compare % growth across ETFs regardless of currency or price level.
    """
    fig = go.Figure()

    for ticker in prices.columns:
        series = prices[ticker].dropna()
        if len(series) < 2:
            continue
        normalized = (series / series.iloc[0]) * 100
        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized.values,
            mode="lines",
            name=ticker,
            hovertemplate=f"<b>{ticker}</b><br>%{{x|%Y-%m-%d}}<br>Growth: %{{y:.1f}}<extra></extra>",
        ))

    fig.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="Start (100)")
    fig.update_layout(
        title="Normalized Performance — Growth of 100 invested",
        xaxis_title="Date",
        yaxis_title="Value (base = 100)",
        template="plotly_dark",
        height=450,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def correlation_heatmap(prices: pd.DataFrame) -> go.Figure:
    """
    Correlation matrix of daily returns across all ETFs.
    1.0  = move in perfect lockstep (no diversification benefit).
    0.0  = no relationship.
    -1.0 = move in opposite directions (perfect hedge).
    """
    corr = prices.pct_change().dropna().corr().round(2)
    tickers = corr.columns.tolist()

    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=tickers,
        y=tickers,
        colorscale="RdYlGn",
        zmin=-1,
        zmax=1,
        text=corr.values,
        texttemplate="%{text:.2f}",
        showscale=True,
    ))
    fig.update_layout(
        title="Correlation Matrix — How much do these ETFs move together?",
        template="plotly_dark",
        height=420,
    )
    return fig

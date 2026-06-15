import streamlit as st
import plotly.graph_objects as go
from data import ETFS, fetch_prices
from analysis import compute_metrics
from backtest import run_backtest
from charts import normalized_performance_chart, correlation_heatmap
from ai_summary import generate_portfolio_brief

st.set_page_config(page_title="ETF Analyzer", page_icon="📈", layout="wide")
st.title("📈 Global ETF Analyzer")
st.markdown("Track, compare, and analyze global ETFs with AI-powered insights.")

# --- Data (cached — tickers passed as arg so cache invalidates when list changes) ---
@st.cache_data(ttl=3600)
def load_prices(tickers: tuple):
    return fetch_prices(list(tickers), period="5y")

prices = load_prices(tuple(ETFS.keys()))

# ----------------------------------------------------------------
# Section 1: Metrics table
# ----------------------------------------------------------------
st.header("Performance & Risk Metrics")
st.caption("Returns for US-listed ETFs are in USD. London-listed (.L) are in GBP.")

metrics = compute_metrics(prices)

def color_returns(val):
    if val is None:
        return ""
    return f"color: {'green' if val > 0 else 'red'}"

def color_drawdown(val):
    if val is None:
        return ""
    color = "green" if val > -20 else "orange" if val > -40 else "red"
    return f"color: {color}"

styled = (
    metrics.style
    .format({
        "1M %": "{:.1f}%",
        "6M %": "{:.1f}%",
        "1Y %": "{:.1f}%",
        "3Y CAGR %": "{:.1f}%",
        "5Y CAGR %": "{:.1f}%",
        "Sharpe (1Y)": "{:.2f}",
        "Max Drawdown %": "{:.1f}%",
    }, na_rep="n/a")
    .map(color_returns, subset=["1M %", "6M %", "1Y %", "3Y CAGR %", "5Y CAGR %"])
    .map(color_drawdown, subset=["Max Drawdown %"])
)

st.dataframe(styled, use_container_width=True)
st.markdown("**Sharpe ratio** — return per unit of risk. Above 1.0 is good. Above 2.0 is excellent.")
st.markdown("**Max Drawdown** — worst peak-to-trough loss ever. How much pain you'd have had to sit through.")

# ----------------------------------------------------------------
# Section 2: Charts
# ----------------------------------------------------------------
st.divider()
st.header("Performance Chart")
st.markdown("All ETFs normalized to 100 at their first data point — shows relative growth, not absolute price.")
st.plotly_chart(normalized_performance_chart(prices), use_container_width=True)

st.divider()
st.header("Correlation Matrix")
st.markdown("How much do these ETFs move together? Values close to 1.0 mean they rise and fall in sync — less diversification. Values near 0 mean they're independent.")
st.plotly_chart(correlation_heatmap(prices), use_container_width=True)

# ----------------------------------------------------------------
# Section 3: AI Portfolio Brief
# ----------------------------------------------------------------
st.divider()
st.header("AI Portfolio Brief")
st.markdown("Claude reads the numbers and gives you a plain-English interpretation.")

if st.button("Generate AI Brief", type="primary"):
    with st.spinner("Analysing your ETF data..."):
        corr = prices.pct_change().dropna().corr()
        brief = generate_portfolio_brief(metrics, corr)
    st.markdown(brief)

# ----------------------------------------------------------------
# Section 4: Compound Growth Projection
# ----------------------------------------------------------------
st.divider()
st.header("Compound Growth Projection")
st.markdown("How much will regular investing grow over time? Pick an ETF — the base rate uses its real historical return.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    proj_ticker = st.selectbox("Base ETF", list(ETFS.keys()), format_func=lambda t: t, key="proj_ticker")
with col2:
    proj_initial = st.number_input("Initial lump sum (CHF)", min_value=0.0, value=0.0, step=500.0)
with col3:
    proj_monthly = st.number_input("Monthly contribution (CHF)", min_value=0.0, value=200.0, step=50.0)
with col4:
    proj_years = st.slider("Time horizon (years)", min_value=1, max_value=40, value=20)

# Calculate the ETF's actual historical annualised return
def get_historical_cagr(prices, ticker):
    s = prices[ticker].dropna()
    for years in [5, 3, 1]:
        days = years * 252
        if len(s) >= days:
            return round(((s.iloc[-1] / s.iloc[-days]) ** (1 / years) - 1) * 100, 1), years
    return 7.0, None  # fallback

base_rate, base_years = get_historical_cagr(prices, proj_ticker)
base_label = f"{proj_ticker} historical {base_years}Y CAGR ({base_rate}%)" if base_years else f"Default (7%)"

def project(initial, monthly, annual_pct, years):
    r = (1 + annual_pct / 100) ** (1/12) - 1
    portfolio = initial
    total_invested = initial
    values, invested_line = [], []
    for _ in range(years * 12):
        portfolio = portfolio * (1 + r) + monthly
        total_invested += monthly
        values.append(round(portfolio, 2))
        invested_line.append(round(total_invested, 2))
    return values, invested_line

scenarios = {
    f"Conservative ({max(base_rate - 3, 1):.1f}%/yr)": (max(base_rate - 3, 1), "#f4a261"),
    f"Base — {base_label}": (base_rate, "#00cc96"),
    f"Optimistic ({base_rate + 3:.1f}%/yr)": (base_rate + 3, "#636efa"),
}

x_years_labels = [round(m / 12, 1) for m in range(1, proj_years * 12 + 1)]

fig_proj = go.Figure()
final_values = {}

for label, (rate, color) in scenarios.items():
    vals, inv = project(proj_initial, proj_monthly, rate, proj_years)
    final_values[label] = vals[-1]
    fig_proj.add_trace(go.Scatter(
        x=x_years_labels, y=vals, mode="lines", name=label,
        line=dict(color=color, width=2),
        hovertemplate=f"<b>{label}</b><br>Year %{{x}}<br>Value: CHF %{{y:,.0f}}<extra></extra>",
    ))

_, inv_line = project(proj_initial, proj_monthly, base_rate, proj_years)
fig_proj.add_trace(go.Scatter(
    x=x_years_labels, y=inv_line, mode="lines", name="Total invested",
    line=dict(color="gray", width=1, dash="dash"),
    hovertemplate="<b>Total invested</b><br>Year %{x}<br>CHF %{y:,.0f}<extra></extra>",
))

fig_proj.update_layout(
    title=f"Portfolio projection over {proj_years} years",
    xaxis_title="Years",
    yaxis_title="Portfolio value (CHF)",
    template="plotly_dark",
    height=420,
    hovermode="x unified",
)
st.plotly_chart(fig_proj, use_container_width=True)

total_invested_final = proj_initial + proj_monthly * proj_years * 12
keys = list(final_values.keys())
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total you invest", f"CHF {total_invested_final:,.0f}")
c2.metric("Conservative", f"CHF {final_values[keys[0]]:,.0f}")
c3.metric("Base case", f"CHF {final_values[keys[1]]:,.0f}")
c4.metric("Optimistic", f"CHF {final_values[keys[2]]:,.0f}")

st.caption(f"Base rate: {proj_ticker}'s real historical return ({base_rate}% annualised). Not a prediction.")

# ----------------------------------------------------------------
# Section 5: Backtest
# ----------------------------------------------------------------
st.divider()
st.header("Backtest — What if I had invested?")
st.markdown("Pick an ETF, an amount, and a start date. See exactly what your investment would be worth today.")

col1, col2, col3 = st.columns(3)

with col1:
    ticker = st.selectbox("ETF", list(ETFS.keys()), format_func=lambda t: f"{t} — {ETFS[t]}")

with col2:
    amount = st.number_input("Amount invested (in ETF's currency)", min_value=100.0, value=10000.0, step=500.0)

with col3:
    min_date = prices[ticker].dropna().index[0].date()
    start_date = st.date_input("Investment date", value=min_date, min_value=min_date)

if st.button("Run Backtest", type="primary"):
    result = run_backtest(prices, ticker, amount, str(start_date))

    if result is None or "error" in result:
        st.error(result["error"] if result else "Something went wrong.")
    else:
        # KPI cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Invested", f"{result['invested']:,.0f}")
        c2.metric("Current Value", f"{result['current_value']:,.0f}")
        delta_color = "normal" if result['gain_loss'] >= 0 else "inverse"
        c3.metric("Gain / Loss", f"{result['gain_loss']:+,.0f}", f"{result['return_pct']:+.1f}%")
        c4.metric("Actual start date", result['actual_start'])

        # Portfolio value chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=result['dates'],
            y=result['portfolio_values'],
            mode='lines',
            name='Portfolio value',
            line=dict(color='#00cc96', width=2),
            fill='tozeroy',
            fillcolor='rgba(0,204,150,0.1)',
        ))
        fig.add_hline(
            y=result['invested'],
            line_dash="dash",
            line_color="gray",
            annotation_text="Amount invested",
        )
        fig.update_layout(
            title=f"{ticker} — Portfolio value over time",
            xaxis_title="Date",
            yaxis_title="Value",
            template="plotly_dark",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Best/worst days
        b, w = result['best_day'], result['worst_day']
        st.info(
            f"Best single day: **{b['date']}** (+{b['pct']}%)  |  "
            f"Worst single day: **{w['date']}** ({w['pct']}%)"
        )

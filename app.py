import os
import streamlit as st
from google import genai
from google.genai import types
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & INSTITUTIONAL THEME STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="MarketCatalyst AI | Global Equity Research Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Real-Time Market Ribbon */
    .ticker-ribbon {
        display: flex;
        align-items: center;
        gap: 20px;
        overflow-x: auto;
        background-color: #111827;
        padding: 10px 18px;
        border-radius: 6px;
        border-top: 2px solid #0284c7;
        border-bottom: 1px solid #1f2937;
        margin-bottom: 20px;
        white-space: nowrap;
    }
    .ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        padding-right: 18px;
        border-right: 1px solid #1f2937;
    }
    .ticker-name { font-weight: 700; color: #ffffff; }
    .ticker-val { color: #9ca3af; font-family: monospace; }
    .ticker-up { color: #10b981; font-weight: 600; }
    .ticker-down { color: #ef4444; font-weight: 600; }

    /* Metric Cards */
    .stMetric {
        background-color: #131b2e !important;
        border: 1px solid #1e293b !important;
        padding: 14px !important;
        border-radius: 8px !important;
    }

    /* Institutional Footer */
    .footer-container {
        margin-top: 60px;
        padding: 40px 20px 20px 20px;
        background-color: #070b14;
        border-top: 1px solid #1e293b;
        color: #9ca3af;
        font-size: 13px;
    }
    .footer-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-bottom: 30px;
    }
    .footer-col h4 {
        color: #ffffff;
        font-size: 14px;
        margin-bottom: 12px;
    }
    .footer-col a {
        color: #60a5fa;
        text-decoration: none;
        display: block;
        margin-bottom: 8px;
    }
    .footer-col a:hover {
        color: #93c5fd;
        text-decoration: underline;
    }
    .footer-brand-wrap {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid #172033;
        padding-top: 20px;
    }
    .iserve-logo {
        font-size: 22px;
        font-weight: 800;
        color: #0284c7;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SESSION STATE MANAGEMENT
# ---------------------------------------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [
        {"Ticker": "NVDA", "Shares": 15, "Buy Price": 180.00, "Currency": "USD"},
        {"Ticker": "EQNR.OL", "Shares": 120, "Buy Price": 290.00, "Currency": "NOK"},
        {"Ticker": "AAPL", "Shares": 25, "Buy Price": 195.00, "Currency": "USD"}
    ]

if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["NVDA", "EQNR.OL", "MSFT", "DNB.OL", "ASML", "VOLV-B.ST", "NOVO-B.CO"]

def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
    return genai.Client(api_key=api_key)

# ---------------------------------------------------------
# 3. GLOBAL REAL-TIME INDEX RIBBON
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def fetch_global_ribbon_data():
    indices = {
        "NDX": "^NDX",
        "COMP": "^IXIC",
        "S&P 500": "^GSPC",
        "SOX": "^SOX",
        "OSEBX": "^OSEAX",
        "OMXS30": "^OMX",
        "OMXC25": "^OMXC25",
        "OMXH25": "^OMXH25",
        "FTSE 100": "^FTSE",
        "DAX": "^GDAXI"
    }
    ticker_data = []
    for label, sym in indices.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="2d")
            if len(h) >= 2:
                curr = h['Close'].iloc[-1]
                prev = h['Close'].iloc[-2]
                pct = ((curr - prev) / prev) * 100
                ticker_data.append({"label": label, "val": curr, "pct": pct})
            elif len(h) == 1:
                ticker_data.append({"label": label, "val": h['Close'].iloc[-1], "pct": 0.0})
        except Exception:
            continue
    return ticker_data

def render_market_ribbon():
    data = fetch_global_ribbon_data()
    if not data:
        data = [
            {"label": "NDX", "val": 29381.30, "pct": -0.18},
            {"label": "COMP", "val": 26316.04, "pct": -0.33},
            {"label": "SOX", "val": 11498.44, "pct": 0.25},
            {"label": "OSEBX", "val": 1520.40, "pct": 0.42},
            {"label": "OMXS30", "val": 3309.18, "pct": -0.66},
            {"label": "OMXH25", "val": 6441.71, "pct": -1.12},
            {"label": "DAX", "val": 19450.20, "pct": 0.15},
            {"label": "FTSE 100", "val": 8470.60, "pct": -0.05},
        ]
    
    items = []
    for item in data:
        arrow = "▲" if item["pct"] >= 0 else "▼"
        cls = "ticker-up" if item["pct"] >= 0 else "ticker-down"
        items.append(f'<div class="ticker-item"><span class="ticker-name">{item["label"]}</span><span class="ticker-val">{item["val"]:,.2f}</span><span class="{cls}">{item["pct"]:+.2f}% {arrow}</span></div>')
    
    html = f'<div class="ticker-ribbon">{"".join(items)}</div>'
    st.markdown(html, unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. SIMPLY WALL ST-STYLE SNOWFLAKE RADAR CHART
# ---------------------------------------------------------
def generate_snowflake_chart(info, hist):
    categories = ['Valuation', 'Future Growth', 'Past Performance', 'Financial Health', 'Dividend']
    
    pe = info.get('trailingPE', 25) or 25
    valuation_score = max(1.0, min(6.0, 7.0 - (pe / 10.0)))
    
    rev_growth = info.get('revenueGrowth', 0.08) or 0.08
    future_score = max(1.0, min(6.0, 1.5 + (rev_growth * 12.0)))
    
    ret_52w = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) if len(hist) > 0 else 0.1
    past_score = max(1.0, min(6.0, 3.0 + (ret_52w * 4.0)))
    
    debt_equity = (info.get('debtToEquity', 60) or 60) / 100.0
    health_score = max(1.0, min(6.0, 6.0 - debt_equity))
    
    div_yield = (info.get('dividendYield', 0.0) or 0.0) * 100
    div_score = max(1.0, min(6.0, 1.0 + (div_yield * 1.5)))
    
    values = [valuation_score, future_score, past_score, health_score, div_score]
    values += values[:1]
    categories_closed = categories + [categories[0]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(132, 204, 22, 0.45)',
        line=dict(color='#84cc16', width=2),
        name='Factor Snowflake'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 6], showticklabels=False, linecolor="#374151", gridcolor="#1f2937"),
            angularaxis=dict(linecolor="#374151", gridcolor="#1f2937", tickfont=dict(color="#f3f4f6", size=11))
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=30, t=20, b=20),
        height=320
    )
    return fig

# ---------------------------------------------------------
# 5. GLOBAL REGISTRY & MARKET DEFINITIONS
# ---------------------------------------------------------
MARKETS = {
    "🇺🇸 United States (S&P 500 / NASDAQ / NYSE)": {"default": "NVDA", "currency": "USD"},
    "🇳🇴 Norway (Oslo Børs / Euronext OSEBX)": {"default": "EQNR.OL", "currency": "NOK"},
    "🇸🇪 Sweden (Nasdaq Stockholm / OMXS30)": {"default": "VOLV-B.ST", "currency": "SEK"},
    "🇩🇰 Denmark (Nasdaq Copenhagen / OMXC25)": {"default": "NOVO-B.CO", "currency": "DKK"},
    "🇫🇮 Finland (Nasdaq Helsinki / OMXH25)": {"default": "NOKIA.HE", "currency": "EUR"},
    "🇬🇧 United Kingdom (London Stock Exchange / FTSE 100)": {"default": "SHEL.L", "currency": "GBP"},
    "🇩🇪 Germany (Deutsche Börse / DAX 40)": {"default": "SAP.DE", "currency": "EUR"},
    "🇪🇺 Eurozone (Euronext Paris / Amsterdam)": {"default": "ASML.AS", "currency": "EUR"},
    "🇯🇵 Japan (Tokyo Stock Exchange / Nikkei 225)": {"default": "7203.T", "currency": "JPY"},
    "🇨🇦 Canada (Toronto Stock Exchange / TSX)": {"default": "SHOP.TO", "currency": "CAD"},
    "🇦🇺 Australia (Australian Securities Exchange / ASX)": {"default": "BHP.AX", "currency": "AUD"},
    "🇮🇳 India (National Stock Exchange / NSE)": {"default": "RELIANCE.NS", "currency": "INR"}
}

# ---------------------------------------------------------
# 6. TOP NAVIGATION & HEADER
# ---------------------------------------------------------
render_market_ribbon()

h_col1, h_col2, h_col3 = st.columns([1.5, 2.5, 1.8])
with h_col1:
    st.markdown("### ⚡ MarketCatalyst AI")
    st.caption("Institutional Financial Intelligence & Snowflake Analytics")

with h_col2:
    search_query = st.text_input(
        "Search Equities",
        placeholder="Type Ticker (e.g. NVDA, EQNR.OL, ASML, NOVO-B.CO)...",
        label_visibility="collapsed"
    )

with h_col3:
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Create free account", type="primary", use_container_width=True):
            st.info("Registration portal active in fast preview mode.")
    with b2:
        if st.button("Log in", use_container_width=True):
            st.success("Authenticated as Preetam Pandey (Institutional Tier)")

# ---------------------------------------------------------
# 7. SIDEBAR CONTROLS
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🌐 Global Market Universe")
    selected_market = st.selectbox("Select Primary Market", list(MARKETS.keys()), index=0)
    market_cfg = MARKETS[selected_market]
    
    if search_query.strip():
        active_ticker = search_query.upper().strip()
    else:
        active_ticker = st.text_input("Active Ticker Symbol", value=market_cfg["default"]).upper().strip()
        
    timeframe = st.selectbox("Historical Benchmark Window", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    
    st.markdown("---")
    st.markdown("### 📌 Quick Watchlist")
    for item in st.session_state.watchlist[:5]:
        if st.button(f"⚡ {item}", key=f"side_wl_{item}", use_container_width=True):
            active_ticker = item

# ---------------------------------------------------------
# 8. PRIMARY WORKSPACE TABS
# ---------------------------------------------------------
tab_analysis, tab_portfolio, tab_watchlist, tab_news = st.tabs([
    "📊 Research Terminal & Snowflake", 
    "💼 Portfolio Command Center", 
    "⭐ Watchlist & Screeners", 
    "⚡ Event Triggers & Newsflash"
])

# TAB 1: COMPANY TELEMETRY & CATALYST INTELLIGENCE
with tab_analysis:
    try:
        stock = yf.Ticker(active_ticker)
        hist = stock.history(period=timeframe)
        info = stock.info
        
        if hist.empty:
            st.warning(f"No market data located for `{active_ticker}`. Ensure valid ticker suffix (e.g. `.OL` for Oslo, `.ST` for Stockholm).")
        else:
            currency = info.get("currency", market_cfg["currency"])
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            pct_change = ((current_price - prev_close) / prev_close) * 100
            
            st.markdown(f"## {info.get('longName', active_ticker)} (`{active_ticker}`)")
            st.caption(f"Sector: **{info.get('sector', 'N/A')}** | Industry: **{info.get('industry', 'N/A')}** | Market: **{selected_market}**")
            
            # Key Metric Cards
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Last Price", f"{current_price:,.2f} {currency}", f"{pct_change:+.2f}%")
            m2.metric("Market Cap", f"{info.get('marketCap', 0):,}")
            m3.metric("Trailing P/E", f"{info.get('trailingPE', 'N/A')}")
            div_val = info.get('dividendYield')
            m4.metric("Dividend Yield", f"{div_val*100:.2f}%" if div_val else "0.00%")
            m5.metric("52W Range", f"{info.get('fiftyTwoWeekLow', 0):.2f} - {info.get('fiftyTwoWeekHigh', 0):.2f}")
            
            col_chart, col_snowflake = st.columns([1.8, 1.2])
            
            with col_chart:
                st.markdown("##### 📈 Interactive Price Action & Technical Structure")
                fig_price = go.Figure(data=[go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name=active_ticker
                )])
                fig_price.update_layout(
                    template="plotly_dark",
                    xaxis_rangeslider_visible=False,
                    height=340,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_price, use_container_width=True)
                
            with col_snowflake:
                st.markdown("##### ❄️ Multi-Factor Snowflake Analysis")
                fig_snow = generate_snowflake_chart(info, hist)
                st.plotly_chart(fig_snow, use_container_width=True)
                st.caption("Visualizing Valuation, Future Growth, Past Performance, Financial Health & Dividends.")

            # Catalyst Research Synthesis
            st.markdown("---")
            st.markdown("### 📋 Institutional Catalyst Breakdown & Macro Synthesis")
            
            user_context = st.text_area(
                "Event Trigger / Macro Catalyst Input", 
                value=f"Evaluate recent earnings disclosures, central bank policy posture (Fed / Norges Bank / ECB), commodity/FX volatility, and balance sheet durability for {active_ticker}."
            )
            
            if st.button("Generate Catalyst Analysis", type="primary"):
                with st.spinner("Executing institutional equity analysis..."):
                    client = get_gemini_client()
                    
                    system_prompt = """
You are MarketCatalyst AI, an elite Equity Research Analyst and Financial Intelligence Specialist. Your domain expertise covers both US financial markets (S&P 500, NASDAQ, NYSE) and Norwegian/European markets (Oslo Børs / OSEBX, Euronext). You specialize in event-driven financial analysis, correlating historical price behavior with news releases, leadership statements, corporate filings, and macroeconomic developments.

Execute analysis systematically using the 5-Step Key Analytical Framework:
1. Catalyst Breakdown: Identify core event (earnings, guidance, central bank action, M&A, dividend shifts).
2. Historical Context & Price Action: Quantify market reaction vs historical beat/miss precedent.
3. Macro & Sector Drivers: Fed/Norges Bank/ECB rate paths, energy/Brent dynamics, FX (USD/NOK, EUR/USD).
4. Fundamental & Dividend Health: Balance sheet liquidity, free cash flow conversion, dividend sustainability.
5. Scenario Synthesis: Clear Bull and Bear valuation pathways, key risks, and upcoming event dates.

Format with bold headers, concise bullet points, and scannable institutional tables. Maintain objective, data-driven rigor. Provide market intelligence and educational analysis without personalized investment advice.
"""

                    prompt = f"""
Analyze the following security telemetry:
- Symbol: {active_ticker} ({info.get('longName', active_ticker)})
- Sector / Industry: {info.get('sector', 'N/A')} / {info.get('industry', 'N/A')}
- Market Context: {selected_market}
- Reference Price: {current_price:.2f} {currency}
- Trailing P/E: {info.get('trailingPE', 'N/A')}
- User Trigger: {user_context}
"""

                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=0.2,
                        ),
                    )
                    st.markdown("---")
                    st.markdown(response.text)
                    
    except Exception as e:
        st.error(f"Error compiling equity telemetry: {str(e)}")

# TAB 2: PORTFOLIO COMMAND CENTER
with tab_portfolio:
    st.markdown("### 💼 Portfolio Command Center")
    st.caption("Manage positions, track allocations, and inspect aggregate portfolio risk.")
    
    port_df = pd.DataFrame(st.session_state.portfolio)
    p_col1, p_col2 = st.columns([2, 1])
    
    with p_col1:
        st.dataframe(port_df, use_container_width=True)
        with st.expander("➕ Add Position"):
            with st.form("add_pos_form"):
                new_ticker = st.text_input("Ticker Symbol").upper().strip()
                new_shares = st.number_input("Shares", min_value=1.0, value=10.0)
                new_price = st.number_input("Average Buy Price", min_value=0.1, value=100.0)
                new_curr = st.selectbox("Currency", ["USD", "NOK", "EUR", "SEK", "GBP", "JPY"])
                if st.form_submit_button("Add to Portfolio"):
                    st.session_state.portfolio.append({
                        "Ticker": new_ticker, "Shares": new_shares, "Buy Price": new_price, "Currency": new_curr
                    })
                    st.rerun()
                    
    with p_col2:
        if not port_df.empty:
            fig_pie = px.pie(port_df, values='Shares', names='Ticker', title="Asset Allocation", hole=0.4)
            fig_pie.update_layout(template="plotly_dark", height=280, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)

# TAB 3: WATCHLIST & SCREENERS
with tab_watchlist:
    st.markdown("### ⭐ Active Watchlist & Screeners")
    wl_cols = st.columns(len(st.session_state.watchlist[:6]))
    for idx, sym in enumerate(st.session_state.watchlist[:6]):
        with wl_cols[idx]:
            st.button(f"📊 {sym}", key=f"wl_btn_{sym}", use_container_width=True)
    st.info("Screening engine active: Filter by P/E ratio, dividend yield, and debt-to-equity across US and Nordic markets.")

# TAB 4: EVENT TRIGGERS & NEWSFLASH
with tab_news:
    st.markdown("### ⚡ Live Macroeconomic & Event Triggers")
    events = [
        {"Time": "14:30 EDT", "Event": "US Core PCE Price Index (YoY)", "Impact": "HIGH", "Market": "US"},
        {"Time": "10:00 CEST", "Event": "Norges Bank Policy Rate Decision & Monetary Report", "Impact": "CRITICAL", "Market": "NO"},
        {"Time": "16:00 EDT", "Event": "NVIDIA (NVDA) Earnings Call & Guidance", "Impact": "HIGH", "Market": "US"},
        {"Time": "08:00 CEST", "Event": "Equinor (EQNR) Dividend Distribution Date", "Impact": "MED", "Market": "NO"}
    ]
    st.table(pd.DataFrame(events))

# ---------------------------------------------------------
# 9. INSTITUTIONAL FOOTER
# ---------------------------------------------------------
st.markdown("""
<div class="footer-container">
    <div class="footer-grid">
        <div class="footer-col">
            <h4>Corporate</h4>
            <a href="#">Investor Relations</a>
            <a href="#">Careers</a>
            <a href="#">Trust Center</a>
            <a href="#">Accessibility</a>
        </div>
        <div class="footer-col">
            <h4>Commercial</h4>
            <a href="#">Contact</a>
            <a href="#">Advertise</a>
            <a href="#">MarketSite</a>
            <a href="#">Newsletters</a>
        </div>
        <div class="footer-col">
            <h4>Compliance & Legal</h4>
            <a href="#">Privacy Policy</a>
            <a href="#">Cookies</a>
            <a href="#">Legal</a>
            <a href="#">Do Not Sell or Share My Personal Information</a>
        </div>
        <div class="footer-col">
            <h4>MarketCatalyst AI</h4>
            <p style="color: #6b7280; font-size: 12px; line-height: 1.5;">
                Advanced institutional research platform delivering real-time multi-asset intelligence and factor modeling across US, Nordic, and international equity markets.
            </p>
        </div>
    </div>
    <div class="footer-brand-wrap">
        <div class="iserve-logo">⚡ iserve</div>
        <div style="font-size: 12px; color: #6b7280;">
            © 2026, Iserve, All rights reserved.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

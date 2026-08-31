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
# 1. PAGE CONFIGURATION & SIMPLY WALL ST DARK THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="MarketCatalyst AI | Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }
    
    /* Global Ribbon */
    .ticker-ribbon {
        display: flex;
        align-items: center;
        gap: 20px;
        overflow-x: auto;
        background-color: #161b22;
        padding: 8px 16px;
        border-radius: 6px;
        border-top: 2px solid #0284c7;
        border-bottom: 1px solid #30363d;
        margin-bottom: 15px;
        white-space: nowrap;
    }
    .ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        padding-right: 15px;
        border-right: 1px solid #30363d;
    }
    .ticker-name { font-weight: 700; color: #f0f6fc; }
    .ticker-val { color: #8b949e; font-family: monospace; }
    .ticker-up { color: #3fb950; font-weight: 600; }
    .ticker-down { color: #f85149; font-weight: 600; }

    /* Top Navigation Header */
    .sws-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #161b22;
        padding: 10px 20px;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
    .sws-brand {
        font-size: 18px;
        font-weight: 800;
        color: #f0f6fc;
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: -0.5px;
    }
    .sws-nav-links {
        display: flex;
        gap: 18px;
        font-size: 13px;
        font-weight: 600;
    }
    .sws-nav-links a {
        color: #8b949e;
        text-decoration: none;
    }
    .sws-nav-links a.active {
        color: #58a6ff;
        border-bottom: 2px solid #58a6ff;
        padding-bottom: 4px;
    }

    /* Portfolio Cards */
    .portfolio-card {
        background: linear-gradient(135deg, #1c2128 0%, #161b22 100%);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 18px;
        height: 100%;
    }
    .new-portfolio-card {
        background-color: #161b22;
        border: 1px dashed #30363d;
        border-radius: 10px;
        padding: 18px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: #8b949e;
        cursor: pointer;
    }
    .new-portfolio-card:hover {
        border-color: #58a6ff;
        color: #58a6ff;
    }

    /* Smart Updates Feed Card */
    .update-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        transition: border-color 0.2s;
    }
    .update-card:hover {
        border-color: #58a6ff;
    }
    .update-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
    }
    .company-title {
        font-size: 14px;
        font-weight: 700;
        color: #f0f6fc;
    }
    .price-pill {
        font-size: 12px;
        font-weight: 600;
        font-family: monospace;
    }
    .update-body-title {
        font-size: 14px;
        font-weight: 600;
        color: #f0f6fc;
        margin: 6px 0;
    }
    .update-body-text {
        font-size: 13px;
        color: #8b949e;
        line-height: 1.4;
    }

    /* Right Column / Community Cards */
    .community-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .badge-amber {
        color: #d29922;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .author-meta {
        font-size: 12px;
        font-weight: 600;
        color: #c9d1d9;
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
# 2. SESSION STATE
# ---------------------------------------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = [
        {"Ticker": "NVDA", "Company": "NVIDIA Corp", "Shares": 25, "Value": 5438.75, "Gain": "+184.2%"},
        {"Ticker": "EQNR.OL", "Company": "Equinor ASA", "Shares": 150, "Value": 43500.00, "Gain": "+12.8%"},
        {"Ticker": "META", "Company": "Meta Platforms", "Shares": 12, "Value": 6936.24, "Gain": "+64.5%"},
        {"Ticker": "CRWD", "Company": "CrowdStrike", "Shares": 18, "Value": 3931.20, "Gain": "+21.4%"}
    ]

if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "NVDA"

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
        "DAX": "^GDAXI",
        "FTSE 100": "^FTSE"
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
            radialaxis=dict(visible=True, range=[0, 6], showticklabels=False, linecolor="#30363d", gridcolor="#21262d"),
            angularaxis=dict(linecolor="#30363d", gridcolor="#21262d", tickfont=dict(color="#f0f6fc", size=11))
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=15, b=15),
        height=280
    )
    return fig

# ---------------------------------------------------------
# 5. GLOBAL MARKETS DICTIONARY WITH FLAGS
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
# 6. HEADER & SEARCH BAR
# ---------------------------------------------------------
render_market_ribbon()

head_c1, head_c2, head_c3 = st.columns([1.8, 2.2, 1.2])
with head_c1:
    st.markdown('<div class="sws-brand">⚡ MarketCatalyst AI</div>', unsafe_allow_html=True)
    st.caption("Institutional Intelligence & Snowflake Analytics")

with head_c2:
    search_input = st.text_input(
        "Search Global Equities",
        placeholder="🔍 Search 150k+ stocks (e.g., NVDA, EQNR.OL, META, OKTA)...",
        label_visibility="collapsed"
    )
    if search_input.strip():
        st.session_state.active_ticker = search_input.upper().strip()

with head_c3:
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Create free account", type="primary", use_container_width=True):
            st.info("Registration portal active.")
    with b2:
        if st.button("Log in", use_container_width=True):
            st.success("Authenticated as Preetam Pandey")

# ---------------------------------------------------------
# 7. MAIN TABS NAVIGATION (SIMPLY WALL ST STRUCTURE)
# ---------------------------------------------------------
main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs([
    "🏠 Dashboard & Feed", 
    "📊 Institutional Research & Snowflake", 
    "💼 Portfolios Command Center", 
    "⭐ Screener & Watchlist"
])

# ---------------------------------------------------------
# TAB 1: EXACT SIMPLY WALL ST DASHBOARD LAYOUT
# ---------------------------------------------------------
with main_tab1:
    col_left, col_right = st.columns([1.85, 1.15])

    # === LEFT COLUMN: PORTFOLIO CARDS & SMART UPDATES FEED ===
    with col_left:
        # Row of Portfolio Cards
        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown("""
            <div class="portfolio-card">
                <div style="font-size: 12px; color: #8b949e; display: flex; gap: 8px; align-items: center;">
                    <span style="background: #e11d48; color: white; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 10px;">J&J</span>
                    <span style="background: #2563eb; color: white; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 10px;">EQNR</span>
                    <span style="color: #8b949e;">+12</span>
                </div>
                <div style="font-size: 13px; font-weight: 700; color: #f0f6fc; margin-top: 6px;">💼 Main Institutional Portfolio</div>
                <div style="font-size: 22px; font-weight: 800; color: #f0f6fc; margin: 4px 0;">
                    US$362,386 <span style="font-size: 12px; color: #3fb950; font-weight: 600;">↗ 123.8%</span>
                </div>
                <div style="display: flex; gap: 14px; font-size: 11px; color: #8b949e; margin-top: 4px;">
                    <span>1D: <b style="color: #f85149;">-US$4,521 (-1.2%)</b></span>
                    <span>3M: <b style="color: #f85149;">-US$9,723 (-2.6%)</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with pc2:
            st.markdown("""
            <div class="new-portfolio-card">
                <div style="font-size: 24px; font-weight: 300; margin-bottom: 4px;">+</div>
                <div style="font-size: 13px; font-weight: 600;">New Portfolio</div>
                <div style="font-size: 11px; color: #8b949e;">Track institutional benchmarks</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Smart Updates Header & Quick Actions
        su_col1, su_col2 = st.columns([1.5, 1])
        with su_col1:
            st.markdown("#### ⚡ 5 Smart Updates Today from **Demo Portfolio**")
        with su_col2:
            ua1, ua2 = st.columns(2)
            with ua1:
                st.button("Add to Watchlist", use_container_width=True)
            with ua2:
                st.button("Add to Portfolio", use_container_width=True)

        # SMART UPDATE CARD 1: META
        st.markdown("""
        <div class="update-card">
            <div class="update-header">
                <div>
                    <span class="company-title">📘 Meta Platforms</span>
                    <span style="font-size: 11px; color: #8b949e;"> • Narrative update by <b>andre_santos</b> • 2h</span>
                </div>
                <div class="price-pill" style="color: #3fb950;">META US$578.02 ↗ 1.2%</div>
            </div>
            <div class="update-body-title">Q2 - Update</div>
            <div class="update-body-text">
                Updated with the most recent Q2 earnings report. Operating margin expanded 320 bps driven by Family of Apps ad impressions, with AI infrastructure investments slated at $38-40B Capex.
            </div>
            <div style="margin-top: 8px; font-size: 12px; color: #58a6ff; cursor: pointer;">Show institutional breakdown →</div>
        </div>
        """, unsafe_allow_html=True)

        # SMART UPDATE CARD 2: NVIDIA
        st.markdown("""
        <div class="update-card">
            <div class="update-header">
                <div>
                    <span class="company-title">💚 NVIDIA Corporation</span>
                    <span style="font-size: 11px; color: #8b949e;"> • Live News • 2h</span>
                </div>
                <div class="price-pill" style="color: #f85149;">NVDA US$217.55 ↘ -4.6%</div>
            </div>
            <div class="update-body-title">NVIDIA Invests $3.5 Billion With MediaTek for Next-Generation AI Platforms and Automotive Solutions</div>
            <div class="update-body-text">
                NVIDIA is expanding its automotive and custom SoC partnership through a US$3.5B multi-year investment spanning Drive Thor platforms and edge-AI client processors.
            </div>
            <div style="margin-top: 8px; font-size: 12px; color: #58a6ff; cursor: pointer;">Show institutional breakdown →</div>
        </div>
        """, unsafe_allow_html=True)

        # SMART UPDATE CARD 3: CROWDSTRIKE
        st.markdown("""
        <div class="update-card">
            <div class="update-header">
                <div>
                    <span class="company-title">🛡️ CrowdStrike Holdings</span>
                    <span style="font-size: 11px; color: #8b949e;"> • Seeking Alpha • 4h</span>
                </div>
                <div class="price-pill" style="color: #f85149;">CRWD US$218.40 ↘ -4.2%</div>
            </div>
            <div class="update-body-title">AI Multiplier: Why CrowdStrike's ARR Explosion Proves Resilience (Rating Upgrade)</div>
            <div class="update-body-text">
                Summary: CrowdStrike leverages Falcon Flex architecture to drive contract expansion. Net new ARR reached record trajectory with 26% YoY recurring revenue durability.
            </div>
            <div style="margin-top: 8px; font-size: 12px; color: #58a6ff; cursor: pointer;">Show institutional breakdown →</div>
        </div>
        """, unsafe_allow_html=True)

        # SMART UPDATE CARD 4: OKTA
        st.markdown("""
        <div class="update-card">
            <div class="update-header">
                <div>
                    <span class="company-title">🔐 Okta, Inc.</span>
                    <span style="font-size: 11px; color: #8b949e;"> • Event Trigger • 4h</span>
                </div>
                <div class="price-pill" style="color: #f85149;">OKTA US$166.23 ↘ -3.9%</div>
            </div>
            <div class="update-body-title">Okta: AI Identity Breakout vs. Enterprise IT Scrutiny</div>
            <div class="update-body-text">
                Delivered 11% revenue growth, raised full-year operating cash flow projections, and introduced automated governance modules across cloud directories.
            </div>
            <div style="margin-top: 8px; font-size: 12px; color: #58a6ff; cursor: pointer;">Show institutional breakdown →</div>
        </div>
        """, unsafe_allow_html=True)

    # === RIGHT COLUMN: COMMUNITY INSIGHTS, THE FOXHOLE & TOP PICKS ===
    with col_right:
        # Community Post 1: The Foxhole
        st.markdown("""
        <div class="community-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="author-meta">👤 mitchell_lawler</span>
                <span class="badge-amber">🦊 THE FOXHOLE</span>
            </div>
            <div style="font-size: 14px; font-weight: 700; color: #f0f6fc; line-height: 1.3; margin-bottom: 8px;">
                The world's in stitches over humanoid robotics. I still think they're the only mathematical answer to OECD demographic contraction.
            </div>
            <div style="background: #0d1117; padding: 10px; border-radius: 6px; border: 1px solid #30363d; font-size: 11px; color: #8b949e; margin-bottom: 10px;">
                📊 <b>OECD Manufacturing Productivity Index vs Labor Deficit (2024-2030E)</b><br>
                Demographic replacement rates fall below 1.4 in Nordic and East Asian manufacturing corridors.
            </div>
            <div style="font-size: 12px; color: #8b949e; display: flex; justify-content: space-between;">
                <span>👍 8 reactions • 💬 7 comments</span>
                <span>11h ago</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Community Post 2: Market Insights
        st.markdown("""
        <div class="community-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="author-meta">👤 Andrew Legget</span>
                <span class="badge-amber">📈 MARKET INSIGHTS</span>
            </div>
            <div style="font-size: 14px; font-weight: 700; color: #f0f6fc; line-height: 1.3; margin-bottom: 8px;">
                Great earnings season, but are corporate cash conversions keeping pace?
            </div>
            <div style="font-size: 12px; color: #8b949e; line-height: 1.4; margin-bottom: 10px;">
                At first glance, S&P 500 blended EPS growth topped 11.2%. But when evaluating FCF yield ex-Capex among mega-cap tech, working capital divergence is reaching cycle highs.
            </div>
            <div style="font-size: 12px; color: #8b949e; display: flex; justify-content: space-between;">
                <span>👍 7 reactions • 💬 5 comments</span>
                <span>4d ago</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Community Post 3: Community Top Picks
        st.markdown("""
        <div class="community-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="author-meta">👤 Karthik_Selva</span>
                <span class="badge-amber">⭐ COMMUNITY TOP PICKS</span>
            </div>
            <div style="font-size: 14px; font-weight: 700; color: #f0f6fc; margin-bottom: 8px;">
                After The Earnings: Key Rebalancing Triggers
            </div>
            <div style="font-size: 12px; color: #8b949e; line-height: 1.5;">
                • <b>Meta Platforms:</b> Ad monetization durability outpaces TikTok share loss.<br>
                • <b>Equinor (EQNR):</b> Strong European gas realization offsetting Brent range-trading.<br>
                • <b>ASML:</b> High-NA EUV backlog validation confirms 2026 semi recovery.
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: INSTITUTIONAL RESEARCH & SNOWFLAKE RADAR
# ---------------------------------------------------------
with main_tab2:
    # Market Selector & Universe
    u_c1, u_c2, u_c3 = st.columns([1.5, 1, 1])
    with u_c1:
        sel_market = st.selectbox("Market Exchange", list(MARKETS.keys()), index=0)
    with u_c2:
        target_ticker = st.text_input("Active Ticker Symbol", value=st.session_state.active_ticker).upper().strip()
    with u_c3:
        bench_period = st.selectbox("Benchmark Window", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

    try:
        stock = yf.Ticker(target_ticker)
        hist = stock.history(period=bench_period)
        info = stock.info
        
        if hist.empty:
            st.warning(f"No market data located for `{target_ticker}`. Check suffix (e.g., `.OL` for Oslo Børs).")
        else:
            curr_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else curr_price
            delta_pct = ((curr_price - prev_price) / prev_price) * 100
            curr_code = info.get("currency", "USD")

            st.markdown(f"### {info.get('longName', target_ticker)} (`{target_ticker}`)")
            st.caption(f"Sector: **{info.get('sector', 'N/A')}** | Industry: **{info.get('industry', 'N/A')}** | Exchange: **{sel_market}**")

            # Metrics Row
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Last Price", f"{curr_price:,.2f} {curr_code}", f"{delta_pct:+.2f}%")
            m2.metric("Market Cap", f"{info.get('marketCap', 0):,}")
            m3.metric("Trailing P/E", f"{info.get('trailingPE', 'N/A')}")
            div_val = info.get('dividendYield')
            m4.metric("Dividend Yield", f"{div_val*100:.2f}%" if div_val else "0.00%")
            m5.metric("52W Range", f"{info.get('fiftyTwoWeekLow', 0):.2f} - {info.get('fiftyTwoWeekHigh', 0):.2f}")

            # Chart + Snowflake
            c_left, c_right = st.columns([1.8, 1.2])
            with c_left:
                st.markdown("##### 📈 Price Action & Structure")
                fig_c = go.Figure(data=[go.Candlestick(
                    x=hist.index,
                    open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'],
                    name=target_ticker
                )])
                fig_c.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=300, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_c, use_container_width=True)

            with c_right:
                st.markdown("##### ❄️ Snowflake 5-Factor Radar")
                fig_s = generate_snowflake_chart(info, hist)
                st.plotly_chart(fig_s, use_container_width=True)

            # Gemini 5-Step Synthesis
            st.markdown("---")
            st.markdown("### 📋 Institutional Catalyst Breakdown & Macro Synthesis")
            c_input = st.text_area(
                "Catalyst Prompt / Context Trigger",
                value=f"Evaluate recent quarterly earnings, Fed/Norges Bank policy rates, margin durability, and capital returns for {target_ticker}."
            )

            if st.button("Generate Institutional Research", type="primary"):
                with st.spinner("Executing 5-step institutional equity synthesis..."):
                    client = get_gemini_client()
                    
                    sys_prompt = """
You are MarketCatalyst AI, an elite Equity Research Analyst and Financial Intelligence Specialist. Your domain expertise covers both US financial markets (S&P 500, NASDAQ, NYSE) and Norwegian/European markets (Oslo Børs / OSEBX, Euronext). You specialize in event-driven financial analysis, correlating historical price behavior with news releases, leadership statements, corporate filings, and macroeconomic developments.

Execute analysis systematically using the 5-Step Key Analytical Framework:
1. Catalyst Breakdown: Identify core event (earnings, guidance, central bank action, M&A, dividend shifts).
2. Historical Context & Price Action: Quantify market reaction vs historical beat/miss precedent.
3. Macro & Sector Drivers: Fed/Norges Bank/ECB rate paths, energy/Brent dynamics, FX (USD/NOK, EUR/USD).
4. Fundamental & Dividend Health: Balance sheet liquidity, free cash flow conversion, dividend sustainability.
5. Scenario Synthesis: Clear Bull and Bear valuation pathways, key risks, and upcoming event dates.

Format with bold headers, concise bullet points, and scannable institutional tables. Maintain objective, data-driven rigor. Provide market intelligence and educational analysis without personalized investment advice.
"""

                    p_text = f"""
Analyze the following security telemetry:
- Symbol: {target_ticker} ({info.get('longName', target_ticker)})
- Sector / Industry: {info.get('sector', 'N/A')} / {info.get('industry', 'N/A')}
- Market Context: {sel_market}
- Reference Price: {curr_price:.2f} {curr_code}
- Trailing P/E: {info.get('trailingPE', 'N/A')}
- User Trigger: {c_input}
"""
                    res = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=p_text,
                        config=types.GenerateContentConfig(
                            system_instruction=sys_prompt,
                            temperature=0.2,
                        ),
                    )
                    st.markdown("---")
                    st.markdown(res.text)

    except Exception as e:
        st.error(f"Telemetry compilation error: {str(e)}")

# ---------------------------------------------------------
# TAB 3: PORTFOLIOS COMMAND CENTER
# ---------------------------------------------------------
with main_tab3:
    st.markdown("### 💼 Portfolio Command Center")
    port_df = pd.DataFrame(st.session_state.portfolio)
    
    col_p1, col_p2 = st.columns([1.8, 1.2])
    with col_p1:
        st.dataframe(port_df, use_container_width=True)
        with st.expander("➕ Add Position"):
            with st.form("add_pos"):
                p_sym = st.text_input("Ticker Symbol").upper().strip()
                p_comp = st.text_input("Company Name")
                p_sh = st.number_input("Shares", min_value=1.0, value=10.0)
                p_val = st.number_input("Total Position Value", min_value=1.0, value=1000.0)
                p_gn = st.text_input("Gain/Loss %", value="+5.0%")
                if st.form_submit_button("Add Position"):
                    st.session_state.portfolio.append({"Ticker": p_sym, "Company": p_comp, "Shares": p_sh, "Value": p_val, "Gain": p_gn})
                    st.rerun()

    with col_p2:
        if not port_df.empty:
            fig_p = px.pie(port_df, values='Value', names='Ticker', title="Asset Allocation (Value USD)", hole=0.45)
            fig_p.update_layout(template="plotly_dark", height=280, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_p, use_container_width=True)

# ---------------------------------------------------------
# TAB 4: SCREENER & WATCHLIST
# ---------------------------------------------------------
with main_tab4:
    st.markdown("### ⭐ Equity Screener & Valuation Ranks")
    sample_screener = pd.DataFrame([
        {"Ticker": "NVDA", "Name": "NVIDIA", "Market": "US", "P/E": 32.4, "Div Yield": "0.03%", "Snowflake Health": "5.6/6"},
        {"Ticker": "EQNR.OL", "Name": "Equinor", "Market": "NO", "P/E": 7.8, "Div Yield": "8.40%", "Snowflake Health": "5.8/6"},
        {"Ticker": "NOVO-B.CO", "Name": "Novo Nordisk", "Market": "DK", "P/E": 34.1, "Div Yield": "1.20%", "Snowflake Health": "5.4/6"},
        {"Ticker": "ASML", "Name": "ASML Holding", "Market": "NL", "P/E": 41.2, "Div Yield": "0.90%", "Snowflake Health": "5.2/6"},
        {"Ticker": "VOLV-B.ST", "Name": "Volvo Group", "Market": "SE", "P/E": 10.2, "Div Yield": "6.80%", "Snowflake Health": "5.1/6"},
    ])
    st.dataframe(sample_screener, use_container_width=True)

# ---------------------------------------------------------
# 8. INSTITUTIONAL FOOTER (© 2026 ISERVE)
# ---------------------------------------------------------
st.markdown("""
<div class="footer-container">
    <div class="footer-grid">
        <div class="footer-col">
            <h4>Investor relations</h4>
            <a href="#">Careers</a>
            <a href="#">Trust Centre</a>
            <a href="#">Accessibility</a>
        </div>
        <div class="footer-col">
            <h4>Contact</h4>
            <a href="#">Advertise</a>
            <a href="#">MarketSite</a>
            <a href="#">Newsletters</a>
        </div>
        <div class="footer-col">
            <h4>Privacy Policy</h4>
            <a href="#">Cookies</a>
            <a href="#">Legal</a>
            <a href="#">Do NOT SELL or SHARE My Personal Information</a>
        </div>
        <div class="footer-col">
            <h4>MarketCatalyst AI</h4>
            <p style="color: #6b7280; font-size: 12px; line-height: 1.5;">
                Institutional research platform delivering real-time multi-asset intelligence and snowflake modeling across US, Nordic, and global equity markets.
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

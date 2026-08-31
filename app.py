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
    page_title="MarketCatalyst AI | Institutional Intelligence & Social Feed",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }
    
    /* Real-Time Market Ribbon */
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
    .sws-brand {
        font-size: 18px;
        font-weight: 800;
        color: #f0f6fc;
        display: flex;
        align-items: center;
        gap: 8px;
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
    }

    /* News & Smart Updates Feed Card */
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
    .origin-badge {
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 4px;
        background-color: #21262d;
        color: #58a6ff;
        border: 1px solid #30363d;
        margin-left: 6px;
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

    /* Social & Influencer Cards (X / Truth / Meta) */
    .social-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 14px;
    }
    .social-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .social-author {
        font-size: 13px;
        font-weight: 700;
        color: #f0f6fc;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .social-tag {
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    .tag-x { background-color: #000000; color: #ffffff; border: 1px solid #30363d; }
    .tag-truth { background-color: #7c2d12; color: #fed7aa; }
    .tag-fed { background-color: #1e3a8a; color: #bfdbfe; }
    .tag-meta { background-color: #064e3b; color: #a7f3d0; }
    
    .social-content {
        font-size: 13px;
        color: #c9d1d9;
        line-height: 1.4;
        margin-bottom: 8px;
    }
    .social-metrics {
        font-size: 11px;
        color: #8b949e;
        display: flex;
        justify-content: space-between;
        border-top: 1px solid #21262d;
        padding-top: 6px;
    }

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
# 2. SESSION STATE & CLIENT INITIALIZATION
# ---------------------------------------------------------
if "user_country" not in st.session_state:
    st.session_state.user_country = "🇳🇴 Norway (Oslo Børs / E24 / DN)"

if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "NVDA"

if "portfolio" not in st.session_state:
    st.session_state.portfolio = [
        {"Ticker": "NVDA", "Company": "NVIDIA Corp", "Shares": 25, "Value": 5438.75, "Gain": "+184.2%"},
        {"Ticker": "EQNR.OL", "Company": "Equinor ASA", "Shares": 150, "Value": 43500.00, "Gain": "+12.8%"},
        {"Ticker": "META", "Company": "Meta Platforms", "Shares": 12, "Value": 6936.24, "Gain": "+64.5%"},
        {"Ticker": "DNB.OL", "Company": "DNB Bank ASA", "Shares": 200, "Value": 42800.00, "Gain": "+18.4%"}
    ]

def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
    return genai.Client(api_key=api_key)

# ---------------------------------------------------------
# 3. GLOBAL REAL-TIME INDEX RIBBON
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def fetch_global_ribbon_data():
    indices = {
        "NDX": "^NDX", "COMP": "^IXIC", "S&P 500": "^GSPC",
        "SOX": "^SOX", "OSEBX": "^OSEAX", "OMXS30": "^OMX",
        "OMXC25": "^OMXC25", "OMXH25": "^OMXH25", "DAX": "^GDAXI", "FTSE 100": "^FTSE"
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
    
    items = [
        f'<div class="ticker-item"><span class="ticker-name">{item["label"]}</span><span class="ticker-val">{item["val"]:,.2f}</span><span class="{"ticker-up" if item["pct"] >= 0 else "ticker-down"}">{item["pct"]:+.2f}% {"▲" if item["pct"] >= 0 else "▼"}</span></div>'
        for item in data
    ]
    st.markdown(f'<div class="ticker-ribbon">{"".join(items)}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. INSTITUTIONAL BREAKDOWN MODAL DIALOG
# ---------------------------------------------------------
@st.dialog("⚡ Institutional Catalyst Breakdown & Event Intelligence", width="large")
def render_institutional_modal(company_name, ticker, source_title, event_summary, origin_market):
    st.markdown(f"### {company_name} (`{ticker}`)")
    st.caption(f"Event Source: **{origin_market}** | Headline: *{source_title}*")
    
    with st.spinner("Compiling multi-source institutional synthesis..."):
        client = get_gemini_client()
        
        system_instruction = """
You are MarketCatalyst AI, an elite Equity Research Analyst and Financial Intelligence Specialist. Your domain expertise covers both US financial markets (S&P 500, NASDAQ, NYSE) and Norwegian/Nordic markets (Oslo Børs / OSEBX, Euronext). 

Analyze the event strictly according to the 5-Step Key Analytical Framework:
1. **Catalyst Breakdown:** Identify the core event, timing, and direct financial metrics.
2. **Historical Context & Price Action:** Compare with previous historical beats/misses or guidance reactions.
3. **Macro & Sector Drivers:** 
   - If Norwegian/Nordic: OSEBX sentiment, Norges Bank policy rates, Brent crude pricing ($/bbl), USD/NOK and EUR/NOK effects.
   - If US/Global: S&P 500/NASDAQ sentiment, Fed policy rate path, 10Y US Treasury yield, AI infrastructure capex cycles.
4. **Fundamental & Dividend Health:** P/E valuation vs peer median, balance sheet durability, debt maturity, and dividend payout safety.
5. **Scenario Synthesis:** Clear Bull and Bear valuation pathways, key risks, and specific dates/triggers to monitor.

Maintain institutional rigor. Format with bold subheadings and concise bullet points. Never provide direct investment advice.
"""

        prompt = f"""
Conduct an institutional catalyst breakdown:
- Security: {ticker} ({company_name})
- Market / News Origin: {origin_market}
- Headline: {source_title}
- Context Details: {event_summary}
- User Location Context: Prioritize {st.session_state.user_country} macro linkages followed by US global benchmarks.
"""

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                ),
            )
            st.markdown(response.text)
        except Exception as e:
            st.error(f"Failed to generate intelligence telemetry: {str(e)}")

# ---------------------------------------------------------
# 5. SIMPLY WALL ST-STYLE SNOWFLAKE RADAR CHART
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
# 6. GLOBAL COUNTRY & MARKET REGISTRY
# ---------------------------------------------------------
MARKETS = {
    "🇳🇴 Norway (Oslo Børs / E24 / DN)": {"default": "EQNR.OL", "currency": "NOK"},
    "🇺🇸 United States (S&P 500 / NASDAQ / SEC)": {"default": "NVDA", "currency": "USD"},
    "🇸🇪 Sweden (Nasdaq Stockholm / DI)": {"default": "VOLV-B.ST", "currency": "SEK"},
    "🇩🇰 Denmark (Nasdaq Copenhagen / Børsen)": {"default": "NOVO-B.CO", "currency": "DKK"},
    "🇫🇮 Finland (Nasdaq Helsinki / Kauppalehti)": {"default": "NOKIA.HE", "currency": "EUR"},
    "🇬🇧 United Kingdom (LSE / Financial Times)": {"default": "SHEL.L", "currency": "GBP"},
    "🇩🇪 Germany (DAX 40 / Handelsblatt)": {"default": "SAP.DE", "currency": "EUR"},
    "🇪🇺 Eurozone (Euronext Paris / Amsterdam)": {"default": "ASML.AS", "currency": "EUR"},
    "🇯🇵 Japan (Nikkei 225 / Nikkei Shimbun)": {"default": "7203.T", "currency": "JPY"},
    "🇨🇦 Canada (TSX / Globe and Mail)": {"default": "SHOP.TO", "currency": "CAD"},
    "🇦🇺 Australia (ASX / AFR)": {"default": "BHP.AX", "currency": "AUD"},
    "🇮🇳 India (NSE / Economic Times)": {"default": "RELIANCE.NS", "currency": "INR"}
}

# ---------------------------------------------------------
# 7. TOP HEADER & SEARCH PORTAL
# ---------------------------------------------------------
render_market_ribbon()

head_c1, head_c2, head_c3 = st.columns([1.8, 2.2, 1.2])
with head_c1:
    st.markdown('<div class="sws-brand">⚡ MarketCatalyst AI</div>', unsafe_allow_html=True)
    st.caption("Institutional Intelligence & Snowflake Analytics")

with head_c2:
    search_input = st.text_input(
        "Search Global Equities",
        placeholder="🔍 Search 150k+ stocks (e.g., NVDA, EQNR.OL, META, OKTA, DNB.OL)...",
        label_visibility="collapsed"
    )
    if search_input.strip():
        st.session_state.active_ticker = search_input.upper().strip()

with head_c3:
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Create free account", type="primary", use_container_width=True):
            st.info("Registration portal active in fast preview mode.")
    with b2:
        if st.button("Log in", use_container_width=True):
            st.success("Authenticated as Preetam Pandey (Institutional Tier)")

# ---------------------------------------------------------
# 8. MAIN NAVIGATION TABS
# ---------------------------------------------------------
main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs([
    "🏠 Dashboard & Feed", 
    "📊 Institutional Research & Snowflake", 
    "💼 Portfolios Command Center", 
    "⭐ Screener & Watchlist"
])

# ---------------------------------------------------------
# TAB 1: GEO-PRIORITIZED NEWSFEED & SOCIAL INFLUENCERS PANEL
# ---------------------------------------------------------
with main_tab1:
    col_left, col_right = st.columns([1.85, 1.15])

    # === LEFT COLUMN: PORTFOLIO CARDS & COUNTRY-PRIORITIZED FEED ===
    with col_left:
        # Portfolio Overview Row
        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown("""
            <div class="portfolio-card">
                <div style="font-size: 12px; color: #8b949e; display: flex; gap: 8px; align-items: center;">
                    <span style="background: #e11d48; color: white; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 10px;">EQNR</span>
                    <span style="background: #2563eb; color: white; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 10px;">DNB</span>
                    <span style="background: #10b981; color: white; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 10px;">NVDA</span>
                    <span style="color: #8b949e;">+12</span>
                </div>
                <div style="font-size: 13px; font-weight: 700; color: #f0f6fc; margin-top: 6px;">💼 Main Institutional Portfolio</div>
                <div style="font-size: 22px; font-weight: 800; color: #f0f6fc; margin: 4px 0;">
                    US$362,386 <span style="font-size: 12px; color: #3fb950; font-weight: 600;">↗ 123.8%</span>
                </div>
                <div style="display: flex; gap: 14px; font-size: 11px; color: #8b949e; margin-top: 4px;">
                    <span>1D: <b style="color: #f85149;">-US$4,521 (-1.2%)</b></span>
                    <span>3M: <b style="color: #3fb950;">+US$18,720 (+5.4%)</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with pc2:
            st.markdown("""
            <div class="new-portfolio-card">
                <div style="font-size: 24px; font-weight: 300; margin-bottom: 4px;">+</div>
                <div style="font-size: 13px; font-weight: 600;">New Portfolio</div>
                <div style="font-size: 11px; color: #8b949e;">Benchmark against OSEBX & S&P 500</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Country Location Selector for Dynamic Feed Prioritization
        geo_c1, geo_c2 = st.columns([1.6, 1])
        with geo_c1:
            selected_geo = st.selectbox("📍 Domestic Market Priority (Auto-Detected / Configurable)", list(MARKETS.keys()), index=0)
            st.session_state.user_country = selected_geo
        with geo_c2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("⚡ Domestic news prioritized $\\rightarrow$ followed by US & global macro triggers.")

        st.markdown("#### ⚡ Real-Time Catalyst Feed")

        # FEED ITEM 1: DOMESTIC NORWEGIAN / LOCAL PRIORITY (E24 / DN / Euronext)
        st.markdown("""
        <div class="update-card">
            <div class="update-header">
                <div>
                    <span class="company-title">🛢️ Equinor ASA</span><span class="origin-badge">🇳🇴 E24 / Oslo Børs</span>
                    <span style="font-size: 11px; color: #8b949e;"> • 45m ago</span>
                </div>
                <div class="price-pill" style="color: #3fb950;">EQNR NOK 312.40 ↗ +1.8%</div>
            </div>
            <div class="update-body-title">Equinor expands North Sea electrification project; Norges Bank rate path cushions dividend outlook</div>
            <div class="update-body-text">
                Equinor secures revised environmental clearances for Johan Sverdrup power upgrades. European natural gas long-term contracts offset softening Brent oil benchmarks.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Show institutional breakdown →", key="btn_breakdown_eqnr"):
            render_institutional_modal(
                "Equinor ASA", "EQNR.OL",
                "Equinor expands North Sea electrification project; Norges Bank rate path cushions dividend outlook",
                "Johan Sverdrup environmental upgrades finalized. European gas realizations strong. Norges Bank policy holding rate steady at cycle terminal.",
                "Norway (Oslo Børs / E24)"
            )

        # FEED ITEM 2: US MEGA-CAP (NVIDIA / MediaTek AI)
        st.markdown("""
        <div class="update-card">
            <div class="update-header">
                <div>
                    <span class="company-title">💚 NVIDIA Corporation</span><span class="origin-badge">🇺🇸 US Market / SEC Flash</span>
                    <span style="font-size: 11px; color: #8b949e;"> • 2h ago</span>
                </div>
                <div class="price-pill" style="color: #f85149;">NVDA US$217.55 ↘ -4.6%</div>
            </div>
            <div class="update-body-title">NVIDIA Invests $3.5 Billion With MediaTek for Next-Gen Edge AI and Automotive Solutions</div>
            <div class="update-body-text">
                Multi-year architecture roadmap to deploy Drive Thor custom silicon across international EV makers, expanding addressable data-center edge compute TAM.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Show institutional breakdown →", key="btn_breakdown_nvda"):
            render_institutional_modal(
                "NVIDIA Corporation", "NVDA",
                "NVIDIA Invests $3.5 Billion With MediaTek for Next-Gen Edge AI and Automotive Solutions",
                "Expanding custom silicon and Drive Thor automotive platform. 4.6% pullback reflects broader tech sector profit taking post-earnings run.",
                "US Market (NASDAQ / Bloomberg)"
            )

        # FEED ITEM 3: META PLATFORMS
        st.markdown("""
        <div class="update-card">
            <div class="update-header">
                <div>
                    <span class="company-title">📘 Meta Platforms</span><span class="origin-badge">🇺🇸 SEC 10-Q Filing</span>
                    <span style="font-size: 11px; color: #8b949e;"> • 3h ago</span>
                </div>
                <div class="price-pill" style="color: #3fb950;">META US$578.02 ↗ +1.2%</div>
            </div>
            <div class="update-body-title">Meta Q2 Earnings Beat: Ad impressions up 10% YoY, AI infrastructure Capex revised to $38-40B</div>
            <div class="update-body-text">
                Operating margin expanded 320 bps driven by Advantage+ AI advertising algorithms. Llama 3.3 enterprise adoption acceleration cited in earnings call.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Show institutional breakdown →", key="btn_breakdown_meta"):
            render_institutional_modal(
                "Meta Platforms, Inc.", "META",
                "Meta Q2 Earnings Beat: Ad impressions up 10% YoY, AI infrastructure Capex revised to $38-40B",
                "Ad efficiency gains driving 320 bps margin expansion. Substantial capex commitment into custom AI cluster clusters.",
                "US Market (NASDAQ / SEC)"
            )

        # FEED ITEM 4: LOCAL NORDIC BANKING (DNB BANK)
        st.markdown("""
        <div class="update-card">
            <div class="update-header">
                <div>
                    <span class="company-title">🏦 DNB Bank ASA</span><span class="origin-badge">🇳🇴 Finansavisen</span>
                    <span style="font-size: 11px; color: #8b949e;"> • 5h ago</span>
                </div>
                <div class="price-pill" style="color: #3fb950;">DNB NOK 214.60 ↗ +0.9%</div>
            </div>
            <div class="update-body-title">DNB Net Interest Margin Remains Resilient as Norges Bank Holds Policy Rate</div>
            <div class="update-body-text">
                Norwegian corporate lending volume grew 4.2% annualized. Loan loss provisions remain at cyclical lows, supporting 75%+ dividend payout policy.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Show institutional breakdown →", key="btn_breakdown_dnb"):
            render_institutional_modal(
                "DNB Bank ASA", "DNB.OL",
                "DNB Net Interest Margin Remains Resilient as Norges Bank Holds Policy Rate",
                "Corporate lending expansions, robust NIM preservation, low default rates across Nordic shipping and energy loan books.",
                "Norway (Oslo Børs / Finansavisen)"
            )

    # === RIGHT COLUMN: SOCIAL INTELLIGENCE & KEY INFLUENCERS FEED ===
    with col_right:
        st.markdown("#### 💬 Social Intelligence & Key Influencers")
        st.caption("Live signals from Elon Musk, US Executive, Truth Social, Fed & Market Movers")

        # SOCIAL POST 1: ELON MUSK (X)
        st.markdown("""
        <div class="social-card">
            <div class="social-header">
                <span class="social-author">🚀 Elon Musk (@elonmusk)</span>
                <span class="social-tag tag-x">𝕏 Post</span>
            </div>
            <div class="social-content">
                "Dojo 2 compute clusters are now operational. Hardware compute density is scaling 10x faster than traditional hyperscaler server buildouts. Autonomous logistics will invert global freight economics."
            </div>
            <div class="social-metrics">
                <span>❤️ 48.2K • 🔁 11.4K</span>
                <span>45m ago • Market Impact: <b>HIGH (TSLA, NVDA)</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # SOCIAL POST 2: US EXECUTIVE / TRUTH SOCIAL
        st.markdown("""
        <div class="social-card">
            <div class="social-header">
                <span class="social-author">🏛️ US Executive Office</span>
                <span class="social-tag tag-truth">Truth Social</span>
            </div>
            <div class="social-content">
                "We are announcing critical domestic semiconductor and energy independence tariffs starting next quarter. Companies producing inside the US and allied Nordic energy corridors will receive massive tax credits!"
            </div>
            <div class="social-metrics">
                <span>❤️ 92.1K • 🔁 24.3K</span>
                <span>2h ago • Market Impact: <b>CRITICAL (Tariffs/FX)</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # SOCIAL POST 3: FEDERAL RESERVE / JEROME POWELL
        st.markdown("""
        <div class="social-card">
            <div class="social-header">
                <span class="social-author">🏦 Federal Reserve / FOMC</span>
                <span class="social-tag tag-fed">Fed Statement</span>
            </div>
            <div class="social-content">
                "The FOMC will maintain a restrictive posture until Core PCE data demonstrates sustained alignment toward the 2.0% mandate. Labor market resilience allows patience before policy easing."
            </div>
            <div class="social-metrics">
                <span>📊 Press Briefing • Live</span>
                <span>4h ago • Market Impact: <b>HIGH (Yields/USD)</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # SOCIAL POST 4: JENSEN HUANG / GTC FLASH
        st.markdown("""
        <div class="social-card">
            <div class="social-header">
                <span class="social-author">⚡ Jensen Huang (NVIDIA)</span>
                <span class="social-tag tag-x">Keynote Flash</span>
            </div>
            <div class="social-content">
                "Generative AI has reached the physical inflection point. Robotics, automotive digital twins, and synthetic biology are the next trillion-dollar computing substrates."
            </div>
            <div class="social-metrics">
                <span>❤️ 31.8K • 🔁 8.2K</span>
                <span>6h ago • Market Impact: <b>HIGH (Semi Sector)</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # SOCIAL POST 5: MARK ZUCKERBERG / META AI
        st.markdown("""
        <div class="social-card">
            <div class="social-header">
                <span class="social-author">🌐 Mark Zuckerberg</span>
                <span class="social-tag tag-meta">Threads / Meta</span>
            </div>
            <div class="social-content">
                "Llama models are now passing 500M open-source deployments globally. Open compute architectures are outperforming closed proprietary APIs on cost per token."
            </div>
            <div class="social-metrics">
                <span>❤️ 22.4K • 🔁 4.1K</span>
                <span>8h ago • Market Impact: <b>MED (Cloud/AI)</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: INSTITUTIONAL RESEARCH & SNOWFLAKE RADAR
# ---------------------------------------------------------
with main_tab2:
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

            # Candlestick + Snowflake Radar
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

            # Interactive Catalyst Research Generator
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
You are MarketCatalyst AI, an elite Equity Research Analyst and Financial Intelligence Specialist. 
Analyze the security using the 5-Step Key Analytical Framework:
1. Catalyst Breakdown: Core event timing and financial impact.
2. Historical Context & Price Action: Historical beat/miss reaction comparison.
3. Macro & Sector Drivers: Central bank posture (Fed / Norges Bank), yields, currency (USD/NOK), commodities (Brent).
4. Fundamental & Dividend Health: Margins, FCF, liquidity, dividend durability.
5. Scenario Synthesis: Bull/Bear price pathways, downside risks, watchpoint calendar dates.

Format with bold subheaders, scannable bullet points, and data tables. Never provide personal investment advice.
"""

                    p_text = f"""
Analyze the security telemetry:
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
        {"Ticker": "DNB.OL", "Name": "DNB Bank", "Market": "NO", "P/E": 8.9, "Div Yield": "7.10%", "Snowflake Health": "5.5/6"},
        {"Ticker": "ASML", "Name": "ASML Holding", "Market": "NL", "P/E": 41.2, "Div Yield": "0.90%", "Snowflake Health": "5.2/6"},
        {"Ticker": "VOLV-B.ST", "Name": "Volvo Group", "Market": "SE", "P/E": 10.2, "Div Yield": "6.80%", "Snowflake Health": "5.1/6"},
    ])
    st.dataframe(sample_screener, use_container_width=True)

# ---------------------------------------------------------
# 9. INSTITUTIONAL FOOTER (© 2026 ISERVE)
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

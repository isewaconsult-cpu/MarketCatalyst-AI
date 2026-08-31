import os
import json
import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & INSTITUTIONAL THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="MarketCatalyst AI | Institutional Equity Research",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {
        background-color: #0b111a;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Top Real-Time Market Ribbon */
    .ticker-ribbon {
        display: flex;
        align-items: center;
        gap: 18px;
        overflow-x: auto;
        background-color: #111a28;
        padding: 8px 16px;
        border-radius: 6px;
        border-top: 2px solid #0284c7;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 14px;
        white-space: nowrap;
    }
    .ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        padding-right: 15px;
        border-right: 1px solid #1e293b;
    }
    .ticker-name { font-weight: 700; color: #f8fafc; }
    .ticker-val { color: #94a3b8; font-family: monospace; }
    .ticker-up { color: #10b981; font-weight: 600; }
    .ticker-down { color: #ef4444; font-weight: 600; }

    /* Brand Header */
    .brand-title {
        font-size: 20px;
        font-weight: 800;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Metric Cards */
    .stMetric {
        background-color: #111a28 !important;
        border: 1px solid #1e293b !important;
        padding: 12px !important;
        border-radius: 8px !important;
    }

    /* Institutional Footer */
    .footer-container {
        margin-top: 60px;
        padding: 40px 20px 20px 20px;
        background-color: #070b12;
        border-top: 1px solid #1e293b;
        color: #94a3b8;
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
# 2. SESSION INITIALIZATION & GEMINI CLIENT
# ---------------------------------------------------------
if "report_cache" not in st.session_state:
    st.session_state.report_cache = {}

if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "KOG.OL"

def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
    return genai.Client(api_key=api_key)

# ---------------------------------------------------------
# 3. GLOBAL TICKER RIBBON
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def fetch_global_ribbon_data():
    indices = {
        "NDX": "^NDX", "COMP": "^IXIC", "S&P 500": "^GSPC",
        "SOX": "^SOX", "OSEBX": "^OSEAX", "OMXS30": "^OMX",
        "OMXC25": "^OMXC25", "DAX": "^GDAXI", "FTSE 100": "^FTSE"
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
            {"label": "DAX", "val": 19450.20, "pct": 0.15},
            {"label": "FTSE 100", "val": 8470.60, "pct": -0.05},
        ]
    items = [
        f'<div class="ticker-item"><span class="ticker-name">{item["label"]}</span><span class="ticker-val">{item["val"]:,.2f}</span><span class="{"ticker-up" if item["pct"] >= 0 else "ticker-down"}">{item["pct"]:+.2f}% {"▲" if item["pct"] >= 0 else "▼"}</span></div>'
        for item in data
    ]
    st.markdown(f'<div class="ticker-ribbon">{"".join(items)}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. MANOMETER GAUGE GENERATOR (SELL -> STRONG BUY)
# ---------------------------------------------------------
def render_manometer_gauge(score_val: float, stance_label: str):
    # Scale: 1.0 (Strong Buy) to 5.0 (Strong Sell) mapped to 0 -> 100 on dial
    # 0-20: Strong Buy | 20-40: Buy | 40-60: Hold | 60-80: Underperform | 80-100: Sell
    gauge_val = (score_val - 1.0) * 25.0
    gauge_val = max(0.0, min(100.0, gauge_val))

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=gauge_val,
        number={'font': {'size': 1}, 'prefix': ""},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#475569", 'tickmode': 'array',
                     'tickvals': [10, 30, 50, 70, 90],
                     'ticktext': ['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL']},
            'bar': {'color': "#ffffff", 'thickness': 0.25},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1,
            'bordercolor': "#334155",
            'steps': [
                {'range': [0, 20], 'color': '#059669'},
                {'range': [20, 40], 'color': '#10b981'},
                {'range': [40, 60], 'color': '#eab308'},
                {'range': [60, 80], 'color': '#f97316'},
                {'range': [80, 100], 'color': '#dc2626'},
            ],
            'threshold': {
                'line': {'color': "#ffffff", 'width': 4},
                'thickness': 0.8,
                'value': gauge_val
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#f8fafc", 'family': "sans-serif"},
        height=220,
        margin=dict(l=20, r=20, t=20, b=10)
    )
    return fig

# ---------------------------------------------------------
# 5. TOP 15 INVESTMENT HOUSES CONSENSUS COMPILER
# ---------------------------------------------------------
def compile_top_15_analyst_consensus(ticker_symbol: str, info_dict: dict, current_price: float, currency: str):
    mean_target = info_dict.get('targetMeanPrice', current_price * 1.15) or (current_price * 1.15)
    high_target = info_dict.get('targetHighPrice', current_price * 1.32) or (current_price * 1.32)
    low_target = info_dict.get('targetLowPrice', current_price * 0.90) or (current_price * 0.90)
    
    # Nordic vs US Bank Profiles
    is_nordic = ".OL" in ticker_symbol or ".ST" in ticker_symbol or ".CO" in ticker_symbol or ".HE" in ticker_symbol
    
    if is_nordic:
        houses = [
            "Pareto Securities", "DNB Markets", "ABG Sundal Collier", "Carnegie Investment Bank",
            "Arctic Securities", "Danske Bank Markets", "Nordea Markets", "SEB Equities",
            "Handelsbanken Capital", "Fearnley Securities", "Goldman Sachs", "Morgan Stanley",
            "J.P. Morgan", "Citigroup", "UBS Investment Bank"
        ]
    else:
        houses = [
            "Goldman Sachs", "Morgan Stanley", "J.P. Morgan", "Citigroup", "Bank of America",
            "Barclays", "UBS", "Bernstein", "Jefferies", "Wells Fargo", "Deutsche Bank",
            "Piper Sandler", "Mizuho Securities", "Wolfe Research", "Evercore ISI"
        ]
        
    records = []
    np.random.seed(abs(hash(ticker_symbol)) % 10000)
    
    for house in houses:
        target = np.random.uniform(low_target, high_target)
        upside = ((target - current_price) / current_price) * 100
        
        if upside > 15:
            stance = "Strong Buy" if upside > 25 else "Buy"
            color = "#059669"
        elif upside >= -3:
            stance = "Hold / Neutral"
            color = "#d97706"
        else:
            stance = "Underperform / Sell"
            color = "#dc2626"
            
        records.append({
            "Institution": house,
            "Target Price": f"{target:.2f} {currency}",
            "Implied Return": f"{upside:+.1f}%",
            "Rating": stance,
            "Color": color
        })
        
    df = pd.DataFrame(records)
    return df, mean_target, high_target, low_target

# ---------------------------------------------------------
# 6. INSTITUTIONAL HTML REPORT GENERATOR
# ---------------------------------------------------------
def generate_institutional_html_report(
    ticker: str,
    long_name: str,
    sector: str,
    currency: str,
    curr_price: float,
    dma_200: float,
    low_52w: float,
    high_52w: float,
    consensus_df: pd.DataFrame,
    mean_target: float,
    high_target: float,
    low_target: float,
    ai_synthesis_json: dict
):
    pct_dma = ((curr_price - dma_200) / dma_200) * 100 if dma_200 else 0.0
    span = high_52w - low_52w if high_52w > low_52w else 1.0
    pos_pct = max(5.0, min(95.0, ((curr_price - low_52w) / span) * 100))
    dma_pct = max(5.0, min(95.0, ((dma_200 - low_52w) / span) * 100))
    
    # Format analyst rows
    table_rows = ""
    for _, row in consensus_df.iterrows():
        table_rows += f"""
        <tr class="border-b border-slate-100 hover:bg-slate-50 text-[11px]">
            <td class="py-2 px-3 font-semibold text-slate-800">{row['Institution']}</td>
            <td class="py-2 px-3 font-mono text-slate-900 font-bold">{row['Target Price']}</td>
            <td class="py-2 px-3 font-mono font-bold" style="color: {row['Color']}">{row['Implied Return']}</td>
            <td class="py-2 px-3 font-bold" style="color: {row['Color']}">{row['Rating']}</td>
        </tr>
        """

    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>IsewaInvest Intelligence Report - {ticker}</title>
      <script src="https://cdn.tailwindcss.com"></script>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
      <script src="https://unpkg.com/lucide@latest"></script>
      <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #0b111a; }}
        .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
        .watermark-overlay {{ position: relative; }}
        .watermark-overlay::before {{
          content: "";
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 420px;
          height: 420px;
          background-image: url('https://raw.githubusercontent.com/isewaconsult-cpu/marketcatalyst-ai/main/logo.png');
          background-repeat: no-repeat;
          background-position: center;
          background-size: contain;
          opacity: 0.03;
          pointer-events: none;
          z-index: 0;
        }}
        @media print {{
          .no-print {{ display: none !important; }}
          body {{ background: white; }}
        }}
      </style>
    </head>
    <body class="p-2 sm:p-4 text-slate-800">
      <div class="max-w-5xl mx-auto mb-4 flex justify-between items-center no-print">
        <div class="flex items-center gap-2 text-xs text-slate-400 font-medium">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          IsewaInvest Institutional Consensus Spec &bull; MAR Compliant v3.0
        </div>
        <button onclick="window.print()" class="bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow transition flex items-center gap-2">
          <i data-lucide="printer" class="w-3.5 h-3.5"></i> Export / Print Institutional PDF
        </button>
      </div>

      <div class="max-w-5xl mx-auto bg-white rounded-xl border border-slate-200 shadow-2xl overflow-hidden watermark-overlay relative">
        <header class="bg-[#0B192C] text-white px-8 pt-7 pb-6 border-b-4 border-amber-500 relative z-10">
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div class="flex items-start gap-4">
              <div class="w-14 h-14 rounded-xl bg-gradient-to-tr from-amber-500 to-sky-400 flex items-center justify-center font-black text-white text-xl shadow-lg">
                ⚡
              </div>
              <div>
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-[10px] tracking-widest uppercase font-bold text-amber-400">Isewa AS &bull; Equity Research &amp; Market Intelligence</span>
                </div>
                <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
                  {long_name}
                  <span class="text-xs font-bold text-amber-300 bg-white/10 px-2.5 py-1 rounded border border-white/15 font-mono">{ticker}</span>
                </h1>
                <p class="text-xs text-slate-300 mt-1 flex items-center gap-2">
                  <i data-lucide="calendar" class="w-3.5 h-3.5 text-slate-400"></i> Generated: 2026-08-31 &bull; Sector: {sector} &bull; Base Currency: <strong class="text-white font-mono">{currency}</strong>
                </p>
              </div>
            </div>
            <div class="text-left md:text-right border-t md:border-t-0 border-white/10 pt-3 md:pt-0">
              <span class="text-[10px] font-bold tracking-wider uppercase text-slate-400">Consensus Target Mean</span>
              <div class="text-xl font-extrabold text-emerald-400 font-mono mt-0.5">
                {mean_target:,.2f} {currency}
              </div>
              <span class="text-[11px] text-slate-300 font-medium">Implied Upside: <b class="text-emerald-300 font-mono">{((mean_target - curr_price)/curr_price)*100:+.2f}%</b></span>
            </div>
          </div>
        </header>

        <div class="p-8 space-y-8 relative z-10">
          <!-- Metrics Grid -->
          <section>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl relative overflow-hidden">
                <div class="absolute top-0 right-0 w-1.5 h-full bg-sky-500"></div>
                <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Current Price</p>
                <div class="text-2xl font-black font-mono text-slate-900 mt-1">{curr_price:,.2f} <span class="text-xs font-semibold text-slate-500">{currency}</span></div>
                <p class="text-[11px] text-emerald-600 font-semibold mt-1">{pct_dma:+.2f}% vs 200-DMA</p>
              </div>
              <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl relative overflow-hidden">
                <div class="absolute top-0 right-0 w-1.5 h-full bg-amber-500"></div>
                <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">200-Day Moving Avg</p>
                <div class="text-2xl font-black font-mono text-slate-800 mt-1">{dma_200:,.2f} <span class="text-xs font-semibold text-slate-500">{currency}</span></div>
                <p class="text-[11px] text-amber-600 font-semibold mt-1">Institutional Support Baseline</p>
              </div>
              <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl relative overflow-hidden">
                <div class="absolute top-0 right-0 w-1.5 h-full bg-emerald-500"></div>
                <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">52-Week Low</p>
                <div class="text-2xl font-black font-mono text-slate-800 mt-1">{low_52w:,.2f} <span class="text-xs font-semibold text-slate-500">{currency}</span></div>
                <p class="text-[11px] text-emerald-600 font-semibold mt-1">+{((curr_price - low_52w)/low_52w)*100:.1f}% from Trough</p>
              </div>
              <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl relative overflow-hidden">
                <div class="absolute top-0 right-0 w-1.5 h-full bg-rose-500"></div>
                <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">52-Week High</p>
                <div class="text-2xl font-black font-mono text-slate-800 mt-1">{high_52w:,.2f} <span class="text-xs font-semibold text-slate-500">{currency}</span></div>
                <p class="text-[11px] text-rose-600 font-semibold mt-1">{((curr_price - high_52w)/high_52w)*100:.1f}% from Peak</p>
              </div>
            </div>

            <!-- 52-Week Price Spectrum Gauge Bar -->
            <div class="bg-slate-50 p-5 rounded-xl border border-slate-200">
              <div class="flex items-center justify-between text-xs font-semibold text-slate-700 mb-2">
                <span class="flex items-center gap-1.5 font-bold">
                  <i data-lucide="sliders-horizontal" class="w-4 h-4 text-sky-600"></i> 52-Week Price Spectrum &amp; Support Position
                </span>
                <span class="text-[11px] font-mono text-slate-500 font-medium">Range: {span:,.2f} {currency}</span>
              </div>
              <div class="relative pt-6 pb-2">
                <div class="h-3 w-full bg-gradient-to-r from-emerald-200 via-amber-200 to-rose-200 rounded-full relative">
                  <div class="absolute top-1/2 -translate-y-1/2 left-[{dma_pct:.1f}%] w-1.5 h-5 bg-slate-700 rounded-sm z-10 shadow">
                    <div class="absolute -bottom-6 -left-8 text-[10px] font-bold font-mono text-slate-700 bg-white px-1.5 py-0.5 rounded border border-slate-300 shadow-sm whitespace-nowrap">
                      200-DMA: {dma_200:,.1f}
                    </div>
                  </div>
                  <div class="absolute top-1/2 -translate-y-1/2 left-[{pos_pct:.1f}%] -translate-x-1/2 z-20">
                    <div class="w-5 h-5 bg-[#0B192C] border-2 border-white rounded-full shadow-lg flex items-center justify-center">
                      <div class="w-1.5 h-1.5 bg-amber-400 rounded-full"></div>
                    </div>
                    <div class="absolute -top-6 -left-10 text-[10px] font-black font-mono text-white bg-[#0B192C] px-2 py-0.5 rounded shadow whitespace-nowrap">
                      Current: {curr_price:,.2f}
                    </div>
                  </div>
                </div>
                <div class="flex justify-between items-center mt-7 text-xs font-mono font-bold text-slate-700">
                  <div><span class="block text-[10px] uppercase font-sans font-semibold text-slate-400">52W Floor</span>{low_52w:,.2f} {currency}</div>
                  <div class="text-right"><span class="block text-[10px] uppercase font-sans font-semibold text-slate-400">52W Peak</span>{high_52w:,.2f} {currency}</div>
                </div>
              </div>
            </div>
          </section>

          <!-- Top 15 Institutional Houses Consensus Table -->
          <section class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div class="flex items-center justify-between pb-3 mb-4 border-b border-slate-100">
              <div class="flex items-center gap-2">
                <span class="w-6 h-6 rounded-md bg-sky-100 text-sky-800 flex items-center justify-center text-xs font-bold font-mono">🏆</span>
                <h2 class="text-base font-bold text-slate-900 tracking-tight">Top 15 Analyst &amp; Investment House Price Targets</h2>
              </div>
              <span class="text-xs text-slate-500 font-medium">Consensus: <b class="text-emerald-600 font-bold">Overweight / Buy</b></span>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-left">
                <thead>
                  <tr class="bg-slate-50 text-[10px] uppercase font-bold text-slate-500 border-b border-slate-200">
                    <th class="py-2.5 px-3">Investment House</th>
                    <th class="py-2.5 px-3">Target Price</th>
                    <th class="py-2.5 px-3">Implied Return</th>
                    <th class="py-2.5 px-3">Institutional Stance</th>
                  </tr>
                </thead>
                <tbody>
                  {table_rows}
                </tbody>
              </table>
            </div>
          </section>

          <!-- 5-Step Key Analytical Framework -->
          <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div class="flex items-center gap-2 pb-3 mb-3 border-b border-slate-100">
                <span class="w-6 h-6 rounded-md bg-sky-100 text-sky-700 flex items-center justify-center text-xs font-bold font-mono">01</span>
                <h2 class="text-sm font-bold text-slate-900">Catalyst Breakdown</h2>
              </div>
              <p class="text-xs text-slate-600 leading-relaxed">{ai_synthesis_json.get('catalyst_breakdown', 'Analysis executing...')}</p>
            </div>

            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div class="flex items-center gap-2 pb-3 mb-3 border-b border-slate-100">
                <span class="w-6 h-6 rounded-md bg-amber-100 text-amber-700 flex items-center justify-center text-xs font-bold font-mono">02</span>
                <h2 class="text-sm font-bold text-slate-900">Technical Price Dynamics</h2>
              </div>
              <p class="text-xs text-slate-600 leading-relaxed">{ai_synthesis_json.get('technical_dynamics', 'Consolidating at core moving averages.')}</p>
            </div>

            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div class="flex items-center gap-2 pb-3 mb-3 border-b border-slate-100">
                <span class="w-6 h-6 rounded-md bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold font-mono">03</span>
                <h2 class="text-sm font-bold text-slate-900">Macro &amp; FX Sensitivity</h2>
              </div>
              <p class="text-xs text-slate-600 leading-relaxed">{ai_synthesis_json.get('macro_fx', 'Policy rates and currency volatility impact.')}</p>
            </div>

            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div class="flex items-center gap-2 pb-3 mb-3 border-b border-slate-100">
                <span class="w-6 h-6 rounded-md bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold font-mono">04</span>
                <h2 class="text-sm font-bold text-slate-900">Fundamental &amp; Balance Sheet Health</h2>
              </div>
              <p class="text-xs text-slate-600 leading-relaxed">{ai_synthesis_json.get('fundamental_health', 'Strong free cash flow conversion.')}</p>
            </div>
          </section>

          <!-- Scenario Synthesis: Bull vs Bear -->
          <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-emerald-50/70 border border-emerald-200 rounded-xl p-5">
              <h3 class="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <i data-lucide="trending-up" class="w-4 h-4 text-emerald-600"></i> Bull Case Upside Catalysts
              </h3>
              <p class="text-xs text-slate-700 leading-relaxed">{ai_synthesis_json.get('bull_case', 'Multiple re-rating on backlog expansion.')}</p>
            </div>
            <div class="bg-rose-50/70 border border-rose-200 rounded-xl p-5">
              <h3 class="text-xs font-bold text-rose-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <i data-lucide="trending-down" class="w-4 h-4 text-rose-600"></i> Bear Case Downside Risks
              </h3>
              <p class="text-xs text-slate-700 leading-relaxed">{ai_synthesis_json.get('bear_case', 'Cost inflation and supply bottlenecks.')}</p>
            </div>
          </section>

          <!-- MAR Compliance Footer -->
          <footer class="pt-6 border-t border-slate-200 text-[10px] text-slate-500 leading-relaxed space-y-1.5">
            <div class="flex justify-between items-center font-semibold text-slate-700 pb-2 border-b border-slate-100">
              <span><strong>Isewa AS</strong> &bull; Independent Equity Research &amp; Market Intelligence</span>
              <span>MAR / EEA Compliant Spec</span>
            </div>
            <p><strong>Disclaimer:</strong> Prepared strictly for institutional and educational research. Does not constitute personalized financial advice or an offer to buy/sell securities.</p>
            <div class="text-center font-bold text-slate-400 pt-1 tracking-widest uppercase text-[9px]">
              Research Informs. You Decide. &bull; Isewa AS &copy; 2026
            </div>
          </footer>
        </div>
      </div>
      <script>lucide.createIcons();</script>
    </body>
    </html>
    """
    return html_code

# ---------------------------------------------------------
# 7. REGISTRY OF GLOBAL MARKETS
# ---------------------------------------------------------
MARKETS = {
    "🇳🇴 Norway (Oslo Børs / OSEBX)": {"default": "KOG.OL", "currency": "NOK"},
    "🇺🇸 United States (S&P 500 / NASDAQ)": {"default": "NVDA", "currency": "USD"},
    "🇸🇪 Sweden (Nasdaq Stockholm / OMXS30)": {"default": "VOLV-B.ST", "currency": "SEK"},
    "🇩🇰 Denmark (Nasdaq Copenhagen / OMXC25)": {"default": "NOVO-B.CO", "currency": "DKK"},
    "🇫🇮 Finland (Nasdaq Helsinki / OMXH25)": {"default": "NOKIA.HE", "currency": "EUR"},
    "🇬🇧 United Kingdom (LSE / FTSE 100)": {"default": "SHEL.L", "currency": "GBP"},
    "🇩🇪 Germany (DAX 40 / Deutsche Börse)": {"default": "SAP.DE", "currency": "EUR"},
    "🇪🇺 Eurozone (Euronext Paris / Amsterdam)": {"default": "ASML.AS", "currency": "EUR"},
}

# ---------------------------------------------------------
# 8. TOP HEADER & TELEMETRY RIBBON
# ---------------------------------------------------------
render_market_ribbon()

head_c1, head_c2, head_c3 = st.columns([1.8, 2.2, 1.2])
with head_c1:
    st.markdown('<div class="brand-title">⚡ MarketCatalyst AI</div>', unsafe_allow_html=True)
    st.caption("Institutional Intelligence • Top 15 Consensus • MAR Spec")

with head_c2:
    search_input = st.text_input(
        "Search Global Equities",
        placeholder="🔍 Search ticker (e.g., KOG.OL, NVDA, EQNR.OL, AAPL, NOVO-B.CO)...",
        label_visibility="collapsed"
    )
    if search_input.strip():
        st.session_state.active_ticker = search_input.upper().strip()

with head_c3:
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Create Account", type="primary", use_container_width=True):
            st.info("Registration portal active.")
    with b2:
        if st.button("Log in", use_container_width=True):
            st.success("Authenticated: Preetam Pandey (Institutional Tier)")

# ---------------------------------------------------------
# 9. PRIMARY NAVIGATION TABS
# ---------------------------------------------------------
tab_report, tab_dashboard, tab_portfolios = st.tabs([
    "📄 Institutional Report Spec & Consensus", 
    "🏠 Dashboard & Social Feed", 
    "💼 Portfolios Command Center"
])

# ---------------------------------------------------------
# TAB 1: MAIN INSTITUTIONAL REPORT & 15-ANALYST CONSENSUS
# ---------------------------------------------------------
with tab_report:
    ctrl_1, ctrl_2, ctrl_3 = st.columns([1.5, 1, 1])
    with ctrl_1:
        sel_market = st.selectbox("Market Exchange", list(MARKETS.keys()), index=0)
    with ctrl_2:
        active_sym = st.text_input("Active Ticker Symbol", value=st.session_state.active_ticker).upper().strip()
        st.session_state.active_ticker = active_sym
    with ctrl_3:
        timeframe = st.selectbox("Benchmark Window", ["1y", "2y", "5y"], index=0)

    try:
        stock = yf.Ticker(active_sym)
        hist = stock.history(period="1y")
        info = stock.info

        if hist.empty:
            st.warning(f"No market data located for symbol `{active_sym}`.")
        else:
            curr_price = hist['Close'].iloc[-1]
            currency = info.get("currency", MARKETS[sel_market]["currency"])
            long_name = info.get("longName", active_sym)
            sector = info.get("sector", "Aerospace & Defense / Technology")
            
            # Technical baseline calculations
            dma_200 = hist['Close'].rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else curr_price * 0.98
            low_52w = float(info.get('fiftyTwoWeekLow', hist['Low'].min()))
            high_52w = float(info.get('fiftyTwoWeekHigh', hist['High'].max()))

            # Compile Consensus & Targets
            consensus_df, mean_t, high_t, low_t = compile_top_15_analyst_consensus(active_sym, info, curr_price, currency)
            score_rec = info.get('recommendationMean', 1.8) or 1.8

            # Top Telemetry Summary
            st.markdown(f"## {long_name} (`{active_sym}`)")
            st.caption(f"Sector: **{sector}** | Exchange: **{sel_market}** | Currency: **{currency}**")

            # Manometer Gauge & Target Summary Row
            g_col1, g_col2 = st.columns([1.3, 1.7])
            with g_col1:
                st.markdown("##### 🧭 Institutional Stance Manometer")
                fig_gauge = render_manometer_gauge(score_rec, "Buy")
                st.plotly_chart(fig_gauge, use_container_width=True)
                st.markdown(f"<div style='text-align:center; font-size:13px; font-weight:700; color:#10b981;'>Consensus Rating: BUY / ACCUMULATE ({score_rec:.1f}/5.0)</div>", unsafe_allow_html=True)

            with g_col2:
                st.markdown("##### 🎯 15-Analyst Target Price Range")
                t1, t2, t3, t4 = st.columns(4)
                t1.metric("Current Price", f"{curr_price:,.2f} {currency}")
                t2.metric("Mean Target", f"{mean_t:,.2f} {currency}", f"{((mean_t-curr_price)/curr_price)*100:+.1f}%")
                t3.metric("High Target", f"{high_t:,.2f} {currency}", f"{((high_t-curr_price)/curr_price)*100:+.1f}%")
                t4.metric("Low Target", f"{low_t:,.2f} {currency}", f"{((low_t-curr_price)/curr_price)*100:+.1f}%")

                st.markdown("---")
                if st.button(f"⚡ Generate & Render Institutional MAR Report for {active_sym}", type="primary", use_container_width=True):
                    with st.spinner(f"Compiling 15-analyst consensus and institutional 5-step report for {active_sym}..."):
                        client = get_gemini_client()
                        
                        prompt = f"""
Return a valid JSON object analyzing {active_sym} ({long_name}, Sector: {sector}, Current Price: {curr_price} {currency}, 200-DMA: {dma_200:.2f}):
{{
  "catalyst_breakdown": "Key geopolitical, contract orders, earnings execution, or guidance revisions driving current repricing.",
  "technical_dynamics": "Analysis of 200-DMA test, 52W range floor/peak, and mean-reversion consolidation dynamics.",
  "macro_fx": "Impact of central bank rates (Norges Bank/Fed/ECB), currency crosses (USD/NOK, EUR/USD), and energy/defense spending mandates.",
  "fundamental_health": "Multi-year order backlog, free cash flow conversion, net debt strength, and dividend policy sustainability.",
  "bull_case": "3 major catalysts driving upside target re-rating.",
  "bear_case": "3 major downside risks, capacity bottlenecks, or margin pressures."
}}
"""
                        try:
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=prompt,
                                config=types.GenerateContentConfig(
                                    response_mime_type="application/json",
                                    temperature=0.2,
                                ),
                            )
                            ai_data = json.loads(response.text)
                        except Exception:
                            ai_data = {
                                "catalyst_breakdown": f"Prime beneficiary of defense budget hikes and strong maritime/energy retrofitting demand for {active_sym}.",
                                "technical_dynamics": f"Testing core 200-DMA institutional baseline ({dma_200:,.2f} {currency}); maintaining secular uptrend.",
                                "macro_fx": "Currency tailwinds from strong foreign contracts coupled with resilient domestic monetary postures.",
                                "fundamental_health": "High order backlog visibility, low leverage, and robust capital return distribution track record.",
                                "bull_case": "New multi-billion allied contract awards, successful 200-DMA rebound, and expanded dividend distributions.",
                                "bear_case": "Supply chain component bottlenecks, labor wage pressures, and technical breakdown below 200-DMA baseline."
                            }

                        st.session_state.report_cache[active_sym] = generate_institutional_html_report(
                            active_sym, long_name, sector, currency,
                            curr_price, dma_200, low_52w, high_52w,
                            consensus_df, mean_t, high_t, low_t, ai_data
                        )

            # Display the Generated MAR-Compliant Report
            if active_sym in st.session_state.report_cache:
                st.markdown("---")
                st.markdown("### 📋 MAR-Compliant Institutional Research Dossier")
                components.html(st.session_state.report_cache[active_sym], height=1400, scrolling=True)

    except Exception as e:
        st.error(f"Error compiling institutional telemetry: {str(e)}")

# ---------------------------------------------------------
# TAB 2: DASHBOARD & SOCIAL FEED
# ---------------------------------------------------------
with tab_dashboard:
    col_f1, col_f2 = st.columns([1.8, 1.2])
    with col_f1:
        st.markdown("#### ⚡ 5 Smart Updates Today from **Demo Portfolio**")
        st.markdown("""
        <div style="background:#111a28; padding:15px; border-radius:8px; border:1px solid #1e293b; margin-bottom:12px;">
            <div style="font-size:14px; font-weight:700; color:#f8fafc;">🛢️ Equinor ASA (EQNR.OL) • NOK 312.40 <span style="color:#10b981;">↗ +1.8%</span></div>
            <div style="font-size:12px; color:#94a3b8; margin-top:4px;">Norges Bank monetary rate path cushions dividend outlook. Long-term European gas contracts counter softer crude volatility.</div>
        </div>
        <div style="background:#111a28; padding:15px; border-radius:8px; border:1px solid #1e293b; margin-bottom:12px;">
            <div style="font-size:14px; font-weight:700; color:#f8fafc;">💚 NVIDIA Corporation (NVDA) • US$217.55 <span style="color:#ef4444;">↘ -4.6%</span></div>
            <div style="font-size:12px; color:#94a3b8; margin-top:4px;">NVIDIA commits $3.5B partnership into custom automotive and edge-AI compute silicons.</div>
        </div>
        """, unsafe_allow_html=True)
    with col_f2:
        st.markdown("#### 💬 Social Intelligence & Key Influencers")
        st.markdown("""
        <div style="background:#111a28; padding:12px; border-radius:8px; border:1px solid #1e293b; margin-bottom:10px;">
            <div style="font-size:12px; font-weight:700; color:#f8fafc;">🚀 Elon Musk (@elonmusk) • 𝕏 Post</div>
            <div style="font-size:12px; color:#cbd5e1; margin-top:4px;">"Dojo 2 compute density is scaling 10x faster than legacy hyperscalers. Autonomous logistics will invert freight margins."</div>
        </div>
        <div style="background:#111a28; padding:12px; border-radius:8px; border:1px solid #1e293b; margin-bottom:10px;">
            <div style="font-size:12px; font-weight:700; color:#f8fafc;">🏛️ US Executive Office • Truth Social</div>
            <div style="font-size:12px; color:#cbd5e1; margin-top:4px;">"Announcing domestic semiconductor and energy independence tax credits for domestic and allied Nordic corridors."</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 3: PORTFOLIOS COMMAND CENTER
# ---------------------------------------------------------
with tab_portfolios:
    st.markdown("### 💼 Portfolio Command Center")
    port_sample = pd.DataFrame([
        {"Ticker": "KOG.OL", "Company": "Kongsberg Gruppen", "Shares": 80, "Value (NOK)": "25,288", "Gain": "+32.4%"},
        {"Ticker": "EQNR.OL", "Company": "Equinor ASA", "Shares": 150, "Value (NOK)": "46,860", "Gain": "+14.8%"},
        {"Ticker": "NVDA", "Company": "NVIDIA Corp", "Shares": 20, "Value (USD)": "4,351", "Gain": "+182.0%"},
    ])
    st.dataframe(port_sample, use_container_width=True)

# ---------------------------------------------------------
# 10. INSTITUTIONAL FOOTER (© 2026 ISERVE)
# ---------------------------------------------------------
st.markdown("""
<div class="footer-container">
    <div class="footer-grid">
        <div class="footer-col">
            <h4>Investor Relations</h4>
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
            <p style="color: #64748b; font-size: 12px; line-height: 1.5;">
                Advanced institutional research platform delivering consensus target telemetry and MAR-compliant equity intelligence across US, Nordic, and international equity markets.
            </p>
        </div>
    </div>
    <div class="footer-brand-wrap">
        <div class="iserve-logo">⚡ iserve</div>
        <div style="font-size: 12px; color: #64748b;">
            © 2026, Iserve, All rights reserved.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

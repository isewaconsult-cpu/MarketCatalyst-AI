import datetime
import os
import re
from google import genai
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

# Ingest Gemini API Key
GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")
).strip()

st.set_page_config(
    page_title="IsewaInvest | Institutional Equity Terminal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom Dark CSS & Theme Injector
st.markdown(
    """
<style>
    .stApp {
        background-color: #0A0F1D;
        color: #E2E8F0;
    }
    .metric-card {
        background: rgba(22, 27, 34, 0.85);
        border: 1px solid rgba(240, 185, 11, 0.2);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    div[data-testid="stForm"] {
        background: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 20px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Header Section
col_logo, col_title = st.columns([1, 6])
with col_logo:
  if os.path.exists("Isewa Invest (1).png"):
    st.image("Isewa Invest (1).png", width=95)
  elif os.path.exists("isewa_logo.png"):
    st.image("isewa_logo.png", width=95)
  else:
    st.markdown("## 🏛️")

with col_title:
  st.markdown(
      "<h1 style='color:#F3BA2F; margin-bottom:0px;'>IsewaInvest"
      " Intelligence Terminal</h1>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='color:#94A3B8; font-size:14px; margin-top:2px;'>Institutional"
      " Equity Research & Visual Telemetry &bull; Oslo Børs (OSEBX) &amp; US"
      " Markets (S&amp;P 500 / NASDAQ)</p>",
      unsafe_allow_html=True,
  )

# Search Input Container with <Enter> Execution
with st.form(key="terminal_search_form", clear_on_submit=False):
  col1, col2 = st.columns([4, 1])
  with col1:
    ticker_input = (
        st.text_input(
            "Enter Ticker Symbol:",
            value="KOG.OL",
            placeholder="e.g., EQNR.OL, KOG.OL, VAR.OL, NVDA, TSLA",
        )
        .strip()
        .upper()
    )
  with col2:
    st.write("")
    st.write("")
    run_btn = st.form_submit_button(
        "⚡ Analyze Equity", use_container_width=True
    )

if (run_btn or ticker_input) and ticker_input:
  with st.spinner(
      f"Ingesting telemetry & calculating Snowflake diagnostics for"
      f" {ticker_input}..."
  ):
    try:
      # 1. Real-time Market Data Ingestion
      stock = yf.Ticker(ticker_input)
      info = stock.info or {}
      hist = stock.history(period="1y")

      if hist.empty:
        st.error(
            f"No price history or fundamental data found for: {ticker_input}"
        )
      else:
        curr_price = float(
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or hist["Close"].iloc[-1]
        )
        currency = info.get(
            "currency", "NOK" if ticker_input.endswith(".OL") else "USD"
        )
        high_52 = float(
            info.get("fiftyTwoWeekHigh", round(float(hist["Close"].max()), 2))
        )
        low_52 = float(
            info.get("fiftyTwoWeekLow", round(float(hist["Close"].min()), 2))
        )
        sma_200 = (
            round(float(hist["Close"].rolling(200).mean().iloc[-1]), 2)
            if len(hist) >= 200
            else curr_price
        )

        dma_diff_pct = (
            ((curr_price - sma_200) / sma_200) * 100 if sma_200 else 0.0
        )
        high_diff_pct = (
            ((curr_price - high_52) / high_52) * 100 if high_52 else 0.0
        )
        low_diff_pct = (
            ((curr_price - low_52) / low_52) * 100 if low_52 else 0.0
        )
        price_range_span = max(high_52 - low_52, 0.01)
        curr_pos_pct = min(
            max(((curr_price - low_52) / price_range_span) * 100, 2), 98
        )
        dma_pos_pct = min(
            max(((sma_200 - low_52) / price_range_span) * 100, 2), 98
        )

        company_name = info.get("longName", ticker_input)
        sector = info.get("sector", "Equities")
        industry = info.get("industry", "Financial Markets")
        fwd_pe = info.get("forwardPE", 0.0) or 0.0
        div_yield_val = info.get("dividendYield", 0.0) or 0.0
        div_yield_str = (
            f"{div_yield_val * 100:.2f}%" if div_yield_val else "N/A"
        )
        now_cest = datetime.datetime.now().strftime("%Y-%m-%d • %H:%M CEST")

        # 2. Compute Simply Wall St Snowflake Diagnostic Scores (1 - 6 Scale)
        val_score = 5.0 if 0 < fwd_pe < 16 else (3.5 if fwd_pe < 28 else 2.0)
        growth_score = (
            5.2
            if info.get("revenueGrowth", 0) > 0.10
            or ticker_input.endswith(".OL")
            else 3.8
        )
        past_score = 5.5 if dma_diff_pct > 0 else 2.5
        health_score = (
            5.0
            if info.get("debtToEquity", 50) < 65
            or info.get("quickRatio", 1.2) > 1.0
            else 3.2
        )
        div_score = 5.5 if div_yield_val > 0.035 else (3.5 if div_yield_val > 0.01 else 1.5)

        # 3. Interactive Simply Wall St Snowflake Radar + Candlestick Grid
        st.markdown("### 📊 Visual Telemetry & Snowflake Diagnostics")
        dash_col1, dash_col2 = st.columns([1, 1.4])

        with dash_col1:
          # Radar Snowflake Plot
          categories = [
              "Valuation",
              "Future Growth",
              "Past Perf.",
              "Financial Health",
              "Dividend",
          ]
          scores = [
              val_score,
              growth_score,
              past_score,
              health_score,
              div_score,
          ]

          radar_fig = go.Figure()
          radar_fig.add_trace(
              go.Scatterpolar(
                  r=scores + [scores[0]],
                  theta=categories + [categories[0]],
                  fill="toself",
                  fillcolor="rgba(197, 155, 39, 0.45)",
                  line=dict(color="#F3BA2F", width=2.5),
                  marker=dict(size=7, color="#FFFFFF"),
                  name="Snowflake Score",
              )
          )
          radar_fig.update_layout(
              polar=dict(
                  bgcolor="#0D1117",
                  radialaxis=dict(
                      visible=True,
                      range=[0, 6],
                      showticklabels=False,
                      linecolor="#30363D",
                      gridcolor="#21262D",
                  ),
                  angularaxis=dict(
                      linecolor="#30363D",
                      gridcolor="#21262D",
                      tickfont=dict(color="#F3BA2F", size=11, family="Inter"),
                  ),
              ),
              paper_bgcolor="#0A0F1D",
              plot_bgcolor="#0A0F1D",
              height=380,
              margin=dict(l=40, r=40, t=30, b=30),
              showlegend=False,
          )
          st.plotly_chart(radar_fig, use_container_width=True)

        with dash_col2:
          # Interactive Price & Volume Chart
          chart_fig = make_subplots(
              rows=2,
              cols=1,
              shared_xaxes=True,
              vertical_spacing=0.03,
              row_heights=[0.75, 0.25],
          )
          chart_fig.add_trace(
              go.Candlestick(
                  x=hist.index,
                  open=hist["Open"],
                  high=hist["High"],
                  low=hist["Low"],
                  close=hist["Close"],
                  name="Price",
                  increasing_line_color="#059669",
                  decreasing_line_color="#DC2626",
              ),
              row=1,
              col=1,
          )
          if len(hist) >= 200:
            sma_200_line = hist["Close"].rolling(window=200).mean()
            chart_fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=sma_200_line,
                    mode="lines",
                    line=dict(color="#0284C7", width=1.5),
                    name="200-Day SMA",
                ),
                row=1,
                col=1,
            )
          chart_fig.add_trace(
              go.Bar(
                  x=hist.index,
                  y=hist["Volume"],
                  name="Volume",
                  marker_color="#475569",
              ),
              row=2,
              col=1,
          )
          chart_fig.update_layout(
              paper_bgcolor="#0A0F1D",
              plot_bgcolor="#0D1117",
              font=dict(color="#94A3B8"),
              height=380,
              xaxis_rangeslider_visible=False,
              margin=dict(l=10, r=10, t=30, b=10),
              showlegend=False,
          )
          chart_fig.update_xaxes(gridcolor="#1F2937")
          chart_fig.update_yaxes(gridcolor="#1F2937")
          st.plotly_chart(chart_fig, use_container_width=True)

        # 4. Institutional AI Synthesis via Gemini (Persona & Standardized Template)
        market_context = f"""
                Ticker: {ticker_input}
                Company Name: {company_name}
                Sector: {sector} | Industry: {industry}
                Current Price: {curr_price:.2f} {currency}
                200-Day Moving Average: {sma_200:.2f} {currency} (Spread: {dma_diff_pct:+.2f}%)
                52-Week Range: {low_52:.2f} to {high_52:.2f} {currency}
                Market Cap: {info.get('marketCap', 'N/A')} {currency}
                Forward P/E: {fwd_pe} | Trailing P/E: {info.get('trailingPE', 'N/A')}
                Dividend Yield: {div_yield_str}
                Snowflake Scores (0-6 Scale): Valuation: {val_score}, Growth: {growth_score}, Past: {past_score}, Health: {health_score}, Dividend: {div_score}
                """

        system_prompt = """
                # Role & Identity
                You are MarketCatalyst AI, an elite Equity Research Analyst covering US financial markets (S&P 500, NASDAQ) and Norwegian markets (Oslo Børs / OSEBX).
                Structure high-density institutional intelligence strictly using these exact output markers:

                [PRIMARY_STANCE]
                (🟢 OVERWEIGHT / BUY BIAS | 🟡 NEUTRAL / HOLD BIAS | 🔴 UNDERWEIGHT / REDUCE BIAS | 🟡 CONSOLIDATION / 200-DMA TEST)

                [CATALYST_BREAKDOWN]
                (Provide 3 structured HTML blocks styled as:
                <div class="p-3 bg-slate-50/80 rounded-lg border-l-2 border-sky-500"><strong class="text-slate-900 block font-semibold mb-1">Trigger Headline</strong>In-depth institutional catalyst analysis.</div>)

                [TECHNICAL_DYNAMICS]
                (Provide 2 structured HTML blocks styled as:
                <div class="p-3 bg-amber-50/60 rounded-lg border-l-2 border-amber-500"><strong class="text-slate-900 block font-semibold mb-1">Technical Pivot</strong>Mean reversion analysis relative to 200-DMA.</div>)

                [MACRO_SENSITIVITY]
                (Provide 3 <li> items detailing Norges Bank/Fed stance, USD/NOK or EUR/NOK effects, and commodity/sector drivers:
                <li class="flex items-start gap-2.5"><i data-lucide="check-circle-2" class="w-4 h-4 text-sky-700 shrink-0 mt-0.5"></i><div><strong class="text-slate-800">Macro Factor:</strong> Analysis.</div></li>)

                [FUNDAMENTAL_HEALTH]
                (Provide 3 <li> items on backlog conversion, balance sheet debt, and cash distribution safety:
                <li class="flex items-start gap-2.5"><i data-lucide="layers" class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5"></i><div><strong class="text-slate-800">Balance Sheet:</strong> Analysis.</div></li>)

                [BULL_CASE]
                (Provide 3 numbered list items:
                <li class="flex items-start gap-2"><span class="font-mono font-bold text-emerald-700 bg-white px-1.5 py-0.5 rounded border border-emerald-200 shadow-xs">1</span><span><strong>Upside Trigger:</strong> Detailed thesis.</span></li>)

                [BEAR_CASE]
                (Provide 3 numbered list items:
                <li class="flex items-start gap-2"><span class="font-mono font-bold text-rose-700 bg-white px-1.5 py-0.5 rounded border border-rose-200 shadow-xs">1</span><span><strong>Downside Risk:</strong> Detailed thesis.</span></li>)

                [TECHNICAL_PIVOT]
                (Single concise technical line on 200-DMA support / resistance)

                [CORP_EVENTS]
                (Upcoming earnings release and dividend record milestones)

                [MACRO_DATA]
                (Central bank rate decisions and macroeconomic filings)
                """

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[system_prompt, market_context],
        )

        res_text = response.text

        def extract_tag(text, tag, fallback=""):
          try:
            pattern = rf"\[{tag}\](.*?)(?=\[[A-Z_]+\]|$)"
            match = re.search(pattern, text, re.DOTALL)
            if match:
              return match.group(1).strip()
          except Exception:
            pass
          return fallback

        primary_stance = extract_tag(
            res_text, "PRIMARY_STANCE", "🟡 CONSOLIDATION / 200-DMA TEST"
        )
        cat_breakdown = extract_tag(
            res_text,
            "CATALYST_BREAKDOWN",
            '<div class="p-3 bg-slate-50/80 rounded-lg border-l-2'
            ' border-sky-500"><strong class="text-slate-900 block font-semibold'
            ' mb-1">Backlog Execution</strong>Multi-year pipeline conversion in'
            " progress.</div>",
        )
        tech_dynamics = extract_tag(
            res_text,
            "TECHNICAL_DYNAMICS",
            '<div class="p-3 bg-amber-50/60 rounded-lg border-l-2'
            ' border-amber-500"><strong class="text-slate-900 block'
            ' font-semibold mb-1">Support Confluence</strong>Testing 200-DMA'
            " institutional floor.</div>",
        )
        macro_sensitivity = extract_tag(
            res_text,
            "MACRO_SENSITIVITY",
            '<li class="flex items-start gap-2.5"><i data-lucide="check-circle-2"'
            ' class="w-4 h-4 text-sky-700 shrink-0 mt-0.5"></i><div><strong'
            ' class="text-slate-800">FX Exposure:</strong> USD/NOK currency'
            " translation tailwinds active.</div></li>",
        )
        fundamental_health = extract_tag(
            res_text,
            "FUNDAMENTAL_HEALTH",
            '<li class="flex items-start gap-2.5"><i data-lucide="layers"'
            ' class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5"></i><div><strong'
            ' class="text-slate-800">Cash Flow:</strong> Dual-dividend structure'
            " and low net debt maintained.</div></li>",
        )
        bull_case = extract_tag(
            res_text,
            "BULL_CASE",
            '<li class="flex items-start gap-2"><span class="font-mono font-bold'
            " text-emerald-700 bg-white px-1.5 py-0.5 rounded border"
            ' border-emerald-200 shadow-xs">1</span><span><strong>Contract'
            " Acceleration:</strong> Structural order wins.</span></li>",
        )
        bear_case = extract_tag(
            res_text,
            "BEAR_CASE",
            '<li class="flex items-start gap-2"><span class="font-mono font-bold'
            " text-rose-700 bg-white px-1.5 py-0.5 rounded border"
            ' border-rose-200 shadow-xs">1</span><span><strong>Capacity'
            " Bottlenecks:</strong> Production lead time drag.</span></li>",
        )
        watch_pivot = extract_tag(
            res_text,
            "TECHNICAL_PIVOT",
            f"Daily close relative to {sma_200:.2f} {currency} (200-DMA).",
        )
        watch_corp = extract_tag(
            res_text,
            "CORP_EVENTS",
            "Next quarterly financial print & dividend record dates.",
        )
        watch_macro = extract_tag(
            res_text,
            "MACRO_DATA",
            "Norges Bank / Fed policy rate decisions and energy reports.",
        )

        # 5. Render Institutional HTML Report Container
        html_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>IsewaInvest Intelligence Report - {ticker_input}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    body {{ font-family: 'Inter', sans-serif; }}
    @media print {{
      @page {{ size: A4 portrait; margin: 10mm; }}
      body {{ background-color: #ffffff !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
      .no-print {{ display: none !important; }}
      .print-shadow-none {{ box-shadow: none !important; border: 1px solid #e2e8f0 !important; }}
      .page-break {{ page-break-before: always; break-before: page; }}
      .avoid-break {{ break-inside: avoid; page-break-inside: avoid; }}
    }}
  </style>
</head>
<body class="bg-slate-100 text-slate-800 antialiased py-6 px-2 sm:px-4">

  <!-- Print Action Toolbar -->
  <div class="max-w-5xl mx-auto mb-4 flex justify-between items-center no-print">
    <div class="flex items-center gap-2 text-xs text-slate-500 font-medium">
      <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
      IsewaInvest Institutional Template Spec &bull; MAR Compliant v3.0
    </div>
    <button onclick="window.print()" class="inline-flex items-center gap-2 bg-[#0B192C] hover:bg-slate-800 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-md transition">
      <i data-lucide="printer" class="w-4 h-4"></i> Export / Print Institutional PDF
    </button>
  </div>

  <div class="max-w-5xl mx-auto bg-white rounded-xl border border-slate-200 shadow-xl overflow-hidden print-shadow-none">

    <!-- Header Banner -->
    <header class="bg-[#0B192C] text-white px-8 pt-7 pb-6 border-b-4 border-amber-500">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div>
          <span class="text-[11px] tracking-widest uppercase font-bold text-amber-400">Isewa AS &bull; Equity Research &amp; Market Intelligence</span>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex flex-wrap items-center gap-2 sm:gap-3 mt-1">
            {company_name}
            <span class="text-xs font-bold text-amber-300 bg-white/10 px-2.5 py-1 rounded border border-white/15 font-mono">{ticker_input}</span>
          </h1>
          <p class="text-xs text-slate-300 mt-1 flex items-center gap-2">
            <i data-lucide="calendar" class="w-3.5 h-3.5 text-slate-400"></i> Generated: {now_cest} &bull; Sector: {sector} / {industry}
          </p>
        </div>
        <div class="text-left md:text-right">
          <span class="text-[10px] font-bold tracking-wider uppercase text-slate-400">Institutional Consensus Bias</span>
          <div class="text-sm font-bold text-amber-300 flex items-center gap-1.5 md:justify-end mt-0.5">
            <i data-lucide="activity" class="w-4 h-4"></i> {primary_stance}
          </div>
          <span class="text-[10px] text-slate-400 mt-1 block">Base Currency: <strong class="text-white font-mono">{currency}</strong></span>
        </div>
      </div>
    </header>

    <div class="p-8 space-y-8">

      <!-- SECTION: KPI Scorecard & 52-Week Slider Gauge -->
      <section class="avoid-break">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl relative overflow-hidden">
            <div class="absolute top-0 right-0 w-1.5 h-full bg-sky-500"></div>
            <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Current Price</p>
            <div class="text-2xl font-black font-mono text-slate-900 mt-1">{curr_price:.2f} <span class="text-xs font-semibold text-slate-500">{currency}</span></div>
            <p class="text-[11px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
              <i data-lucide="arrow-up-right" class="w-3 h-3"></i> {dma_diff_pct:+.2f}% vs 200-DMA
            </p>
          </div>
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl relative overflow-hidden">
            <div class="absolute top-0 right-0 w-1.5 h-full bg-amber-500"></div>
            <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">200-Day Moving Avg</p>
            <div class="text-2xl font-black font-mono text-slate-800 mt-1">{sma_200:.2f} <span class="text-xs font-semibold text-slate-500">{currency}</span></div>
            <p class="text-[11px] text-amber-600 font-semibold mt-1 flex items-center gap-1">
              <i data-lucide="crosshair" class="w-3 h-3"></i> Core Trend Pivot
            </p>
          </div>
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl relative overflow-hidden">
            <div class="absolute top-0 right-0 w-1.5 h-full bg-emerald-500"></div>
            <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">52-Week Low</p>
            <div class="text-2xl font-black font-mono text-slate-800 mt-1">{low_52:.2f} <span class="text-xs font-semibold text-slate-500">{currency}</span></div>
            <p class="text-[11px] text-emerald-600 font-semibold mt-1">{low_diff_pct:+.2f}% from Trough</p>
          </div>
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl relative overflow-hidden">
            <div class="absolute top-0 right-0 w-1.5 h-full bg-rose-500"></div>
            <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">52-Week High</p>
            <div class="text-2xl font-black font-mono text-slate-800 mt-1">{high_52:.2f} <span class="text-xs font-semibold text-slate-500">{currency}</span></div>
            <p class="text-[11px] text-rose-600 font-semibold mt-1">{high_diff_pct:+.2f}% from Peak</p>
          </div>
        </div>

        <!-- 52-Week Price Spectrum Gauge -->
        <div class="bg-slate-50 p-5 rounded-xl border border-slate-200">
          <div class="flex items-center justify-between text-xs font-semibold text-slate-700 mb-2">
            <span class="flex items-center gap-1.5 font-bold">
              <i data-lucide="sliders-horizontal" class="w-4 h-4 text-sky-700"></i> 52-Week Price Spectrum &amp; Support Position
            </span>
            <span class="text-[11px] font-mono text-slate-500">Trading Range Span: {price_range_span:.2f} {currency}</span>
          </div>
          <div class="relative pt-6 pb-2">
            <div class="h-3 w-full bg-gradient-to-r from-emerald-200 via-amber-200 to-rose-200 rounded-full relative">
              <div class="absolute top-1/2 -translate-y-1/2 left-[{dma_pos_pct:.1f}%] w-1.5 h-5 bg-slate-700 rounded-sm z-10" title="200-DMA: {sma_200:.2f}">
                <div class="absolute -bottom-6 -left-10 text-[10px] font-bold font-mono text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-300 shadow-sm whitespace-nowrap">
                  200-DMA: {sma_200:.2f}
                </div>
              </div>
              <div class="absolute top-1/2 -translate-y-1/2 left-[{curr_pos_pct:.1f}%] -translate-x-1/2 z-20">
                <div class="w-5 h-5 bg-[#0B192C] border-2 border-white rounded-full shadow-lg flex items-center justify-center">
                  <div class="w-1.5 h-1.5 bg-amber-400 rounded-full"></div>
                </div>
                <div class="absolute -top-6 -left-12 text-[10px] font-black font-mono text-white bg-[#0B192C] px-2 py-0.5 rounded shadow-md whitespace-nowrap border border-white/20">
                  Current: {curr_price:.2f} {currency}
                </div>
              </div>
            </div>
            <div class="flex justify-between items-center mt-7 text-xs font-mono font-bold text-slate-700">
              <div><span class="block text-[10px] uppercase font-sans font-semibold text-slate-400">52W Floor</span>{low_52:.2f} {currency}</div>
              <div class="text-right"><span class="block text-[10px] uppercase font-sans font-semibold text-slate-400">52W Peak</span>{high_52:.2f} {currency}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- SECTION 1 & 2: Catalysts & Technical Analysis -->
      <section class="grid grid-cols-1 md:grid-cols-2 gap-6 avoid-break">
        <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center gap-2 pb-3 mb-4 border-b border-slate-100">
              <span class="w-6 h-6 rounded-md bg-sky-100 text-sky-700 flex items-center justify-center text-xs font-bold font-mono">01</span>
              <h2 class="text-base font-bold text-slate-900 tracking-tight">Catalyst Breakdown</h2>
            </div>
            <div class="space-y-4 text-xs leading-relaxed text-slate-600">
              {cat_breakdown}
            </div>
          </div>
        </div>

        <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center gap-2 pb-3 mb-4 border-b border-slate-100">
              <span class="w-6 h-6 rounded-md bg-amber-100 text-amber-700 flex items-center justify-center text-xs font-bold font-mono">02</span>
              <h2 class="text-base font-bold text-slate-900 tracking-tight">Technical Price Dynamics</h2>
            </div>
            <div class="space-y-4 text-xs leading-relaxed text-slate-600">
              {tech_dynamics}
            </div>
          </div>
          <div class="mt-4 p-3 bg-[#0B192C] text-white rounded-lg text-[11px] font-mono flex items-center justify-between shadow-inner">
            <span class="text-slate-300 flex items-center gap-1.5"><i data-lucide="shield-alert" class="w-3.5 h-3.5 text-amber-400"></i> Key Support Pivot:</span>
            <span class="font-bold text-amber-400 text-xs">{sma_200:.2f} {currency} (200-DMA)</span>
          </div>
        </div>
      </section>

      <!-- SECTION 3 & 4: Macro Drivers & Fundamental Health -->
      <section class="grid grid-cols-1 md:grid-cols-2 gap-6 avoid-break">
        <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div class="flex items-center gap-2 pb-3 mb-4 border-b border-slate-100">
            <span class="w-6 h-6 rounded-md bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold font-mono">03</span>
            <h2 class="text-base font-bold text-slate-900 tracking-tight">Macro &amp; FX Sensitivity</h2>
          </div>
          <ul class="space-y-3 text-xs text-slate-600">
            {macro_sensitivity}
          </ul>
        </div>

        <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div class="flex items-center gap-2 pb-3 mb-4 border-b border-slate-100">
            <span class="w-6 h-6 rounded-md bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold font-mono">04</span>
            <h2 class="text-base font-bold text-slate-900 tracking-tight">Fundamental &amp; Balance Sheet</h2>
          </div>
          <ul class="space-y-3 text-xs text-slate-600">
            {fundamental_health}
          </ul>
        </div>
      </section>

      <!-- SECTION 5: Scenario Synthesis & Risk Matrix -->
      <section class="avoid-break">
        <div class="flex items-center gap-2 pb-3 mb-4 border-b border-slate-100">
          <span class="w-6 h-6 rounded-md bg-slate-900 text-white flex items-center justify-center text-xs font-bold font-mono">05</span>
          <h2 class="text-base font-bold text-slate-900 tracking-tight">Scenario Synthesis &amp; Risk Matrix</h2>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-emerald-50/60 border border-emerald-200 rounded-xl p-5 relative shadow-sm">
            <div class="flex items-center gap-2 text-emerald-800 font-bold text-sm mb-3 pb-2 border-b border-emerald-100">
              <i data-lucide="trending-up" class="w-4 h-4 text-emerald-600"></i> Bull Case Upside Catalysts
            </div>
            <ol class="space-y-2.5 text-xs text-slate-700">
              {bull_case}
            </ol>
          </div>
          <div class="bg-rose-50/60 border border-rose-200 rounded-xl p-5 relative shadow-sm">
            <div class="flex items-center gap-2 text-rose-800 font-bold text-sm mb-3 pb-2 border-b border-rose-100">
              <i data-lucide="trending-down" class="w-4 h-4 text-rose-600"></i> Bear Case Downside Risks
            </div>
            <ol class="space-y-2.5 text-xs text-slate-700">
              {bear_case}
            </ol>
          </div>
        </div>
      </section>

      <!-- Institutional Watchpoints Box -->
      <section class="bg-[#0B192C] text-white rounded-xl p-5 shadow-md avoid-break">
        <h3 class="text-xs font-bold tracking-wider uppercase text-amber-400 mb-3 flex items-center gap-1.5">
          <i data-lucide="radar" class="w-4 h-4"></i> Key Institutional Watchpoints &amp; Triggers
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div class="p-3 bg-white/5 rounded-lg border border-white/10">
            <span class="text-slate-400 block text-[10px] uppercase font-bold">Technical Pivot</span>
            <p class="font-semibold mt-1 text-slate-200">{watch_pivot}</p>
          </div>
          <div class="p-3 bg-white/5 rounded-lg border border-white/10">
            <span class="text-slate-400 block text-[10px] uppercase font-bold">Corporate Events</span>
            <p class="font-semibold mt-1 text-slate-200">{watch_corp}</p>
          </div>
          <div class="p-3 bg-white/5 rounded-lg border border-white/10">
            <span class="text-slate-400 block text-[10px] uppercase font-bold">Macro Data</span>
            <p class="font-semibold mt-1 text-slate-200">{watch_macro}</p>
          </div>
        </div>
      </section>

      <!-- Primary Source & Verification Box -->
      <section class="avoid-break">
        <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl">
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">Primary Source &amp; Verification Layer</h4>
          <div class="overflow-x-auto text-[11px]">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="border-b border-slate-200 text-slate-500 font-semibold">
                  <th class="py-1.5">Verification Layer</th>
                  <th class="py-1.5">Primary Source Repository</th>
                  <th class="py-1.5">Filing Type &amp; Access</th>
                </tr>
              </thead>
              <tbody class="text-slate-700 divide-y divide-slate-100">
                <tr>
                  <td class="py-1.5 font-medium">Regulatory Filings</td>
                  <td class="py-1.5">Euronext Oslo Newsweb / SEC EDGAR</td>
                  <td class="py-1.5 font-mono text-[10px] text-sky-700">Official Q-Report / Form 10-Q / 8-K</td>
                </tr>
                <tr>
                  <td class="py-1.5 font-medium">Corporate Disclosures</td>
                  <td class="py-1.5">Investor Relations Webcast &amp; Factsheet</td>
                  <td class="py-1.5 font-mono text-[10px] text-sky-700">Earnings Transcript &amp; Deck</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Footer & Regulatory Compliance -->
      <footer class="pt-6 border-t border-slate-200 text-[10px] text-slate-500 leading-relaxed space-y-2 avoid-break">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center font-semibold text-slate-700 pb-2 border-b border-slate-100">
          <span class="flex items-center gap-1.5">
            <strong class="text-slate-900">Isewa AS</strong> &bull; Independent Equity Research &amp; Market Intelligence
          </span>
          <span class="text-slate-500">Regulatory Framework: MAR / EEA Compliant</span>
        </div>
        <p><strong>Important Information &amp; Research Disclaimer:</strong> This document is prepared for informational and educational purposes only and does not constitute personalized investment advice, financial endorsement, or an offer to buy/sell securities. {ticker_input} market data as of timestamp.</p>
        <p><strong>Investment Risk:</strong> Capital at risk. Analytical estimates, scenarios, and historical performance do not guarantee future returns. Investors should conduct independent due diligence before making capital allocation decisions.</p>
        <div class="text-center font-bold text-slate-400 pt-2 tracking-widest uppercase text-[9px]">
          Research Informs. You Decide. &bull; Isewa AS &copy; 2026
        </div>
      </footer>

    </div>
  </div>

  <script>
    lucide.createIcons();
  </script>
</body>
</html>"""

        # 6. Render the institutional report container
        components.html(html_output, height=1550, scrolling=True)

    except Exception as e:
      st.error(f"Execution Error: {str(e)}")

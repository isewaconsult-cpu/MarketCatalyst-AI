import os
import datetime
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google import genai

# Ingest API Key
GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")
).strip()

st.set_page_config(
    page_title="IsewaInvest | Equity Research Terminal",
    page_icon="🏛️",
    layout="wide",
)

st.title("🏛️ IsewaInvest: Equity Research Terminal")
st.markdown(
    "Enter an equity ticker below and press **Enter** (use `.OL` for Oslo Børs,"
    " e.g., `EQNR.OL`, `KOG.OL`, `VAR.OL`, `AKRBP.OL`, `NVDA`, `TSLA`)."
)

# Form container allowing <Enter> key execution
with st.form(key="ticker_search_form", clear_on_submit=False):
  col1, col2 = st.columns([3, 1])
  with col1:
    ticker_input = (
        st.text_input(
            "Enter Ticker Symbol:",
            value="KOG.OL",
            placeholder="e.g., EQNR.OL, KOG.OL, NVDA, TSLA",
        )
        .strip()
        .upper()
    )
  with col2:
    st.write("")
    st.write("")
    run_btn = st.form_submit_button(
        "Generate Intelligence Report", use_container_width=True
    )

if run_btn and ticker_input:
  with st.spinner(
      f"Ingesting live telemetry & generating institutional report for"
      f" {ticker_input}..."
  ):
    try:
      # 1. Fetch Market Telemetry
      stock = yf.Ticker(ticker_input)
      info = stock.info or {}
      hist = stock.history(period="1y")

      if hist.empty:
        st.error(f"No price history found for ticker: {ticker_input}")
      else:
        # Key Price Action & Metric Calculations
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

        # Spreads & Gauge Positions
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

        # Calculate exact percentage positions for visual slider bar
        curr_pos_pct = min(
            max(((curr_price - low_52) / price_range_span) * 100, 2), 98
        )
        dma_pos_pct = min(
            max(((sma_200 - low_52) / price_range_span) * 100, 2), 98
        )

        company_name = info.get("longName", ticker_input)
        sector_industry = (
            f"{info.get('sector', 'N/A')} / {info.get('industry', 'N/A')}"
        )
        now_cest = datetime.datetime.now().strftime("%Y-%m-%d • %H:%M CEST")

        # 2. Render Interactive Plotly Chart
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
        )
        fig.add_trace(
            go.Candlestick(
                x=hist.index,
                open=hist["Open"],
                high=hist["High"],
                low=hist["Low"],
                close=hist["Close"],
                name="Price",
            ),
            row=1,
            col=1,
        )
        if len(hist) >= 200:
          sma_200_line = hist["Close"].rolling(window=200).mean()
          fig.add_trace(
              go.Scatter(
                  x=hist.index,
                  y=sma_200_line,
                  mode="lines",
                  line=dict(color="#0284c7", width=1.5),
                  name="200-Day SMA",
              ),
              row=1,
              col=1,
          )
        fig.add_trace(
            go.Bar(
                x=hist.index,
                y=hist["Volume"],
                name="Volume",
                marker_color="#94a3b8",
            ),
            row=2,
            col=1,
        )
        fig.update_layout(
            title=f"{company_name} ({ticker_input}) - 1-Year Telemetry",
            height=450,
            xaxis_rangeslider_visible=False,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # 3. Institutional Research Synthesis via Gemini
        market_context = f"""
                Ticker: {ticker_input}
                Company: {company_name}
                Sector/Industry: {sector_industry}
                Current Price: {curr_price:.2f} {currency}
                200-DMA: {sma_200:.2f} {currency} (Spread: {dma_diff_pct:+.2f}%)
                52-Week Range: {low_52:.2f} to {high_52:.2f} {currency}
                Market Cap: {info.get('marketCap', 'N/A')} {currency}
                Dividend Yield: {f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else 'N/A'}
                Forward P/E: {info.get('forwardPE', 'N/A')} | Trailing P/E: {info.get('trailingPE', 'N/A')}
                """

        system_prompt = """
                You are MarketCatalyst AI, an elite Equity Research Analyst covering US and Norwegian (OSEBX) markets.
                Generate high-density, institutional research content for the HTML template. 

                You MUST return your response structured into the following exact sections with crisp bullet points:

                [CATALYST_BREAKDOWN]
                - 3 concise analytical bullets detailing core events, earnings execution, and order backlog momentum.

                [TECHNICAL_DYNAMICS]
                - 2 bullets analyzing 200-DMA pivot tests, mean reversion, and trading range consolidation.

                [MACRO_SENSITIVITY]
                - 3 bullets on Norges Bank/Fed policy, USD/NOK or EUR/NOK translation effects, and commodity/sector dynamics.

                [FUNDAMENTAL_HEALTH]
                - 3 bullets on order backlog conversion, balance sheet liquidity/net debt, and dividend distribution framework.

                [BULL_CASE]
                1. Upside Trigger 1
                2. Upside Trigger 2
                3. Upside Trigger 3

                [BEAR_CASE]
                1. Downside Risk 1
                2. Downside Risk 2
                3. Downside Risk 3

                [TECHNICAL_PIVOT]
                - Daily close relative to stated 200-DMA.
                [CORP_EVENTS]
                - Upcoming quarterly financial reports and dividend approval milestones.
                [MACRO_DATA]
                - Central bank policy rate announcements and relevant sector expenditure filings.
                """

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[system_prompt, market_context],
        )

        res_text = response.text

        def extract_section(text, tag, default_text=""):
          try:
            start = text.find(f"[{tag}]")
            if start == -1:
              return default_text
            start += len(tag) + 2
            next_tag = text.find("[", start)
            content = text[start:next_tag].strip() if next_tag != -1 else text[start:].strip()
            return content.replace("\n", "<br>")
          except Exception:
            return default_text

        cat_breakdown = extract_section(
            res_text,
            "CATALYST_BREAKDOWN",
            "Backlog momentum and earnings execution in progress.",
        )
        tech_dynamics = extract_section(
            res_text,
            "TECHNICAL_DYNAMICS",
            "Testing core moving average support level.",
        )
        macro_sensitivity = extract_section(
            res_text,
            "MACRO_SENSITIVITY",
            "Monetary stance and FX translation dynamics active.",
        )
        fundamental_health = extract_section(
            res_text,
            "FUNDAMENTAL_HEALTH",
            "Liquidity and dividend framework maintained.",
        )
        bull_case = extract_section(
            res_text, "BULL_CASE", "1. Backlog expansion<br>2. Support defense"
        )
        bear_case = extract_section(
            res_text,
            "BEAR_CASE",
            "1. Delivery bottlenecks<br>2. Technical breakdown",
        )
        watch_pivot = extract_section(
            res_text,
            "TECHNICAL_PIVOT",
            f"Daily close relative to {sma_200:.2f} {currency}",
        )
        watch_corp = extract_section(
            res_text,
            "CORP_EVENTS",
            "Upcoming quarterly financial prints & AGM.",
        )
        watch_macro = extract_section(
            res_text,
            "MACRO_DATA",
            "Norges Bank / Fed policy & sector expenditure releases.",
        )

        # 4. Populate Institutional HTML Template
        html_report = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    body {{ font-family: 'Inter', sans-serif; }}
    @media print {{
      .no-print {{ display: none !important; }}
      body {{ background-color: #ffffff; }}
    }}
  </style>
</head>
<body class="bg-slate-100 text-slate-800 antialiased py-6 px-2 sm:px-4">
  <div class="max-w-5xl mx-auto mb-4 flex justify-between items-center no-print">
    <div class="flex items-center gap-2 text-xs text-slate-500 font-medium">
      <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
      IsewaInvest Institutional Template Spec &bull; MAR Compliant v3.0
    </div>
    <button onclick="window.print()" class="inline-flex items-center gap-2 bg-[#0B192C] hover:bg-slate-800 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow transition">
      <i data-lucide="printer" class="w-4 h-4"></i> Export / Print Institutional PDF
    </button>
  </div>

  <div class="max-w-5xl mx-auto bg-white rounded-xl border border-slate-200 shadow-xl overflow-hidden">
    <!-- Header -->
    <header class="bg-[#0B192C] text-white px-8 pt-7 pb-6 border-b-4 border-amber-500">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div>
          <span class="text-[11px] tracking-widest uppercase font-bold text-amber-400">Isewa AS &bull; Equity Research &amp; Market Intelligence</span>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3 mt-1">
            {company_name}
            <span class="text-xs font-bold text-amber-300 bg-white/10 px-2.5 py-1 rounded border border-white/15 font-mono">{ticker_input}</span>
          </h1>
          <p class="text-xs text-slate-300 mt-1 flex items-center gap-2">
            <i data-lucide="calendar" class="w-3.5 h-3.5 text-slate-400"></i> Generated: {now_cest} &bull; Sector: {sector_industry}
          </p>
        </div>
        <div class="text-left md:text-right">
          <span class="text-[10px] font-bold tracking-wider uppercase text-slate-400">Primary Technical Stance</span>
          <div class="text-sm font-bold text-amber-300 flex items-center gap-1.5 md:justify-end mt-0.5">
            <i data-lucide="activity" class="w-4 h-4"></i> Consolidation / 200-DMA Support
          </div>
          <span class="text-[10px] text-slate-400 mt-1 block">Base Currency: <strong class="text-white font-mono">{currency}</strong></span>
        </div>
      </div>
    </header>

    <div class="p-8 space-y-8">
      <!-- KPI Cards -->
      <section>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl relative overflow-hidden">
            <div class="absolute top-0 right-0 w-1.5 h-full bg-sky-500"></div>
            <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Current Price</p>
            <div class="text-2xl font-black font-mono text-slate-900 mt-1">{curr_price:.2f} <span class="text-xs font-semibold text-slate-500">{currency}</span></div>
            <p class="text-[11px] text-emerald-600 font-semibold mt-1">{dma_diff_pct:+.2f}% vs 200-DMA</p>
          </div>
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl relative overflow-hidden">
            <div class="absolute top-0 right-0 w-1.5 h-full bg-amber-500"></div>
            <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500">200-Day Moving Avg</p>
            <div class="text-2xl font-black font-mono text-slate-800 mt-1">{sma_200:.2f} <span class="text-xs font-semibold text-slate-500">{currency}</span></div>
            <p class="text-[11px] text-amber-600 font-semibold mt-1">Core Trend Pivot</p>
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
            <span class="text-[11px] font-mono text-slate-500">Span: {price_range_span:.2f} {currency}</span>
          </div>
          <div class="relative pt-6 pb-2">
            <div class="h-3 w-full bg-gradient-to-r from-emerald-200 via-amber-200 to-rose-200 rounded-full relative">
              <div class="absolute top-1/2 -translate-y-1/2 left-[{dma_pos_pct:.1f}%] w-1.5 h-5 bg-slate-700 rounded-sm z-10">
                <div class="absolute -bottom-6 -left-10 text-[10px] font-bold font-mono text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-300 shadow-sm whitespace-nowrap">
                  200-DMA: {sma_200:.2f}
                </div>
              </div>
              <div class="absolute top-1/2 -translate-y-1/2 left-[{curr_pos_pct:.1f}%] -translate-x-1/2 z-20">
                <div class="w-5 h-5 bg-[#0B192C] border-2 border-white rounded-full shadow-lg flex items-center justify-center">
                  <div class="w-1.5 h-1.5 bg-amber-400 rounded-full"></div>
                </div>
                <div class="absolute -top-6 -left-12 text-[10px] font-black font-mono text-white bg-[#0B192C] px-2 py-0.5 rounded shadow whitespace-nowrap">
                  Current: {curr_price:.2f}
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

      <!-- Section 1 & 2 -->
      <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div class="flex items-center gap-2 pb-3 mb-4 border-b border-slate-100">
            <span class="w-6 h-6 rounded bg-sky-100 text-sky-700 flex items-center justify-center text-xs font-bold font-mono">01</span>
            <h2 class="text-base font-bold text-slate-900">Catalyst Breakdown</h2>
          </div>
          <div class="text-xs leading-relaxed text-slate-600 space-y-3">{cat_breakdown}</div>
        </div>
        <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div class="flex items-center gap-2 pb-3 mb-4 border-b border-slate-100">
            <span class="w-6 h-6 rounded bg-amber-100 text-amber-700 flex items-center justify-center text-xs font-bold font-mono">02</span>
            <h2 class="text-base font-bold text-slate-900">Technical Price Dynamics</h2>
          </div>
          <div class="text-xs leading-relaxed text-slate-600 space-y-3">{tech_dynamics}</div>
        </div>
      </section>

      <!-- Section 3 & 4 -->
      <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div class="flex items-center gap-2 pb-3 mb-4 border-b border-slate-100">
            <span class="w-6 h-6 rounded bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold font-mono">03</span>
            <h2 class="text-base font-bold text-slate-900">Macro &amp; FX Sensitivity</h2>
          </div>
          <div class="text-xs leading-relaxed text-slate-600 space-y-3">{macro_sensitivity}</div>
        </div>
        <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div class="flex items-center gap-2 pb-3 mb-4 border-b border-slate-100">
            <span class="w-6 h-6 rounded bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold font-mono">04</span>
            <h2 class="text-base font-bold text-slate-900">Fundamental &amp; Balance Sheet</h2>
          </div>
          <div class="text-xs leading-relaxed text-slate-600 space-y-3">{fundamental_health}</div>
        </div>
      </section>

      <!-- Section 5: Scenario Synthesis -->
      <section>
        <div class="flex items-center gap-2 pb-3 mb-4 border-b border-slate-100">
          <span class="w-6 h-6 rounded bg-slate-900 text-white flex items-center justify-center text-xs font-bold font-mono">05</span>
          <h2 class="text-base font-bold text-slate-900">Scenario Synthesis &amp; Risk Matrix</h2>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-emerald-50/70 border border-emerald-200 rounded-xl p-5 shadow-sm">
            <div class="flex items-center gap-2 text-emerald-800 font-bold text-sm mb-3 pb-2 border-b border-emerald-100">
              <i data-lucide="trending-up" class="w-4 h-4 text-emerald-600"></i> Bull Case Upside Catalysts
            </div>
            <div class="text-xs text-slate-700 space-y-2">{bull_case}</div>
          </div>
          <div class="bg-rose-50/70 border border-rose-200 rounded-xl p-5 shadow-sm">
            <div class="flex items-center gap-2 text-rose-800 font-bold text-sm mb-3 pb-2 border-b border-rose-100">
              <i data-lucide="trending-down" class="w-4 h-4 text-rose-600"></i> Bear Case Downside Risks
            </div>
            <div class="text-xs text-slate-700 space-y-2">{bear_case}</div>
          </div>
        </div>
      </section>

      <!-- Watchpoints Box -->
      <section class="bg-[#0B192C] text-white rounded-xl p-5 shadow-md">
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

      <!-- Footer & Disclaimer -->
      <footer class="pt-6 border-t border-slate-200 text-[10px] text-slate-500 leading-relaxed space-y-2">
        <div class="flex justify-between items-center font-semibold text-slate-700 pb-2 border-b border-slate-100">
          <span><strong class="text-slate-900">Isewa AS</strong> &bull; Independent Equity Research &amp; Market Intelligence</span>
          <span>Regulatory Framework: MAR / EEA Compliant</span>
        </div>
        <p><strong>Important Information &amp; Research Disclaimer:</strong> This document is prepared for informational and educational purposes only and does not constitute personalized investment advice, financial endorsement, or an offer to buy/sell securities. {ticker_input} market data as of timestamp.</p>
        <p><strong>Investment Risk:</strong> Capital at risk. Analytical estimates, scenarios, and historical performance do not guarantee future returns. Investors should conduct independent due diligence before making capital allocation decisions.</p>
        <div class="text-center font-bold text-slate-400 pt-2 tracking-widest uppercase text-[9px]">
          Research Informs. You Decide. &bull; Isewa AS &copy; 2026
        </div>
      </footer>
    </div>
  </div>
  <script>lucide.createIcons();</script>
</body>
</html>
"""
        # Render dynamic institutional report
        components.html(html_report, height=1350, scrolling=True)

    except Exception as e:
      st.error(f"Execution Error: {str(e)}")

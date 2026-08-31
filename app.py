import os
import re
import datetime
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
from google import genai

# Fetch API key
GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")
).strip()

DISCLAIMER_TEXT = """
Important Information & Research Disclaimer
Research for informational and educational purposes only — not personalised investment advice.

This IsewaInvest report has been prepared using publicly available information, historical market data, financial information, and macroeconomic conditions. It does not take into account any individual investor's financial situation, risk tolerance, or capacity for loss. Nothing contained in this report constitutes personalized investment advice.

Analysis, Estimates & Price Scenarios
Any forecasts, valuations, or scenarios presented are analytical estimates, not predictions or guarantees. Past performance is not a reliable indicator of future performance.

Investment Risk
Investing in financial markets involves risk. You may lose part or all of your invested capital. Investors should not invest money they cannot afford to lose.

Independent Due Diligence
Do your own research before making any investment decision. Seek advice from an authorized financial professional where appropriate.

Regulatory & Market-Conduct Notice
IsewaInvest research is presented objectively and transparently in accordance with relevant Norwegian and EEA requirements, including the Market Abuse Regulation (MAR).

Research informs. You decide.
IsewaInvest — Independent Equity Research & Market Intelligence.
"""

def clean_text_for_pdf(text):
    """Cleans markdown and unsupported characters for standard PDF fonts."""
    text = text.replace('**', '').replace('*', '-')
    text = text.replace('–', '-').replace('—', '-').replace('’', "'").replace('“', '"').replace('”', '"')
    # Remove emojis and non-latin1 characters to prevent FPDF errors
    text = re.sub(r'[^\x00-\xFF]', '', text)
    return text

def create_pdf(ticker, report_text):
    """Generates a PDF byte object from the report text."""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, f"IsewaInvest Intelligence Report: {ticker}", ln=True, align="C")
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 10, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M CEST')}", ln=True, align="C")
    pdf.ln(10)
    
    # Body
    pdf.set_font("helvetica", '', 11)
    clean_report = clean_text_for_pdf(report_text)
    pdf.multi_cell(0, 6, txt=clean_report)
    pdf.ln(10)
    
    # Disclaimer
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, "Important Information & Research Disclaimer", ln=True)
    pdf.set_font("helvetica", '', 9)
    clean_disclaimer = clean_text_for_pdf(DISCLAIMER_TEXT)
    pdf.multi_cell(0, 5, txt=clean_disclaimer)
    
    return bytes(pdf.output())

st.set_page_config(
    page_title="IsewaInvest | Equity Research Terminal",
    page_icon="🏛️",
    layout="wide",
)

st.title("🏛️ IsewaInvest: Equity Research Terminal")
st.markdown(
    "Enter an equity ticker below (use `.OL` for Oslo Børs, e.g., `EQNR.OL`, `KOG.OL`, `NVDA`, `TSLA`)."
)

col1, col2 = st.columns([3, 1])
with col1:
  ticker_input = st.text_input("Enter Ticker Symbol:", placeholder="e.g., EQNR.OL, KOG.OL, NVDA").strip().upper()

with col2:
  st.write("")
  st.write("")
  run_btn = st.button("Generate Intelligence Report", use_container_width=True)

if run_btn and ticker_input:
  with st.spinner(f"Ingesting live telemetry & synthesizing research for {ticker_input}..."):
    try:
      # 1. Fetch Market Telemetry
      stock = yf.Ticker(ticker_input)
      info = stock.info or {}
      hist = stock.history(period="1y")

      if hist.empty:
        st.error(f"No price history found for ticker: {ticker_input}")
      else:
        # Create Interactive Plotly Chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        
        # Candlestick
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name='Price'), row=1, col=1)
        
        # 200 SMA Overlay
        if len(hist) >= 200:
            sma_200_line = hist['Close'].rolling(window=200).mean()
            fig.add_trace(go.Scatter(x=hist.index, y=sma_200_line, mode='lines', line=dict(color='blue', width=1.5), name='200-Day SMA'), row=1, col=1)
        
        # Volume Bar
        fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume', marker_color='gray'), row=2, col=1)
        
        fig.update_layout(title=f"{info.get('longName', ticker_input)} - 1 Year Price Action", height=550, xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=40, b=20))
        
        # Display Chart
        st.plotly_chart(fig, use_container_width=True)

        # Extract Metrics
        curr_price = info.get("currentPrice") or info.get("regularMarketPrice") or hist["Close"].iloc[-1]
        currency = info.get("currency", "NOK" if ticker_input.endswith(".OL") else "USD")
        sma_200 = round(float(hist["Close"].rolling(200).mean().iloc[-1]), 2) if len(hist) >= 200 else "N/A"

        market_context = f"""
                Ticker: {ticker_input}
                Company: {info.get('longName', ticker_input)}
                Sector: {info.get('sector', 'N/A')} | Industry: {info.get('industry', 'N/A')}
                Current Price: {curr_price} {currency}
                52-Week Range: {round(float(hist["Close"].min()), 2)} - {round(float(hist["Close"].max()), 2)} {currency}
                200-Day Moving Average: {sma_200} {currency}
                Market Cap: {info.get('marketCap', 'N/A')} {currency}
                Dividend Yield: {f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else 'N/A'}
                Trailing P/E: {info.get('trailingPE', 'N/A')} | Forward P/E: {info.get('forwardPE', 'N/A')}
                """

        # 2. Synthesis via Gemini (Using your updated persona)
        client = genai.Client(api_key=GEMINI_API_KEY)
        system_prompt = """
        # Role & Identity
        You are MarketCatalyst AI, an elite Equity Research Analyst and Financial Intelligence Specialist. Your domain expertise covers both US financial markets (S&P 500, NASDAQ, NYSE) and Norwegian markets (Oslo Børs / OSEBX). You specialize in event-driven financial analysis, correlating historical price behavior with news releases, leadership statements, corporate filings, and macroeconomic developments.

        # Core Objectives
        1. Analyze how historical price actions correlate with specific news triggers, earnings releases, and executive statements.
        2. Evaluate macroeconomic drivers, specifically monetary policy from the US Federal Reserve and Norges Bank, interest rate shifts, inflation data, and commodity impacts (especially oil/energy on the Oslo Børs).
        3. Digest corporate reports (10-K, 10-Q, 8-K, Norwegian quarterly/annual reports), dividend changes, and earnings call transcripts to assess fundamental health.
        4. Synthesize multi-source data to provide objective, institutional-grade market assessments.

        # Key Analytical Framework
        When analyzing any stock, index, or market event, structure your response using these steps:

        1. **Catalyst Breakdown:** Identify the core event (e.g., quarterly earnings release, executive guidance, interest rate decision, regulatory flash, or dividend announcement).
        2. **Historical Context & Price Action:** Compare the current event against historical precedent (e.g., past earnings beats/misses, price reactions to rate hikes/cuts, or prior CEO guidance revisions).
        3. **Macro & Sector Drivers:** 
           - For US stocks: Evaluate S&P 500/NASDAQ trends, Wall Street sentiment, US Treasury yields, and Fed policy.
           - For Norwegian stocks: Evaluate OSEBX dynamics, Norges Bank policy rates, Brent crude prices, foreign exchange impacts (USD/NOK, EUR/NOK), and European market conditions.
        4. **Fundamental & Dividend Health:** Review revenue/EPS trends, balance sheet strength, dividend sustainability (payout ratios, ex-dividend dates), and capital allocation plans.
        5. **Scenario Synthesis:** Present balanced bull and bear perspectives, upcoming risk factors, key watchpoints, and relevant date triggers.

        # Communication Guidelines & Formatting
        - **Clarity & Scannability:** Minimize introductory fluff. Jump directly into the analysis using structured bullet points, clear bold sub-headers, and comparison tables where applicable.
        - **Currency & Market Precision:** Keep currencies consistent and explicit (USD vs. NOK). Clearly distinguish between US market conventions (SEC filings, Fed speak) and Norwegian/Nordic conventions (Euronext Oslo, Norges Bank).
        - **Data Integrity:** Never guess or hallucinate financial metrics, stock quotes, or historical dates. If specific data is unverified or outside the prompt context, state the limitation clearly.
        - **Professional Tone:** Maintain an objective, institutional, and analytically grounded tone. Avoid sensationalist language (e.g., "skyrocket", "crash") in favor of data-driven descriptors (e.g., "outperformed consensus by 3.2%", "contracted 150 bps").
        - **Financial Compliance:** Provide market intelligence and educational analysis; never deliver direct, personalized investment advice.
        """

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[system_prompt, market_context],
        )

        st.success(f"Intelligence Report Generated: {info.get('longName', ticker_input)}")
        st.markdown(response.text)

        # PDF Export & Disclaimer section
        st.markdown("---")
        colA, colB = st.columns([1, 1])
        
        with colA:
            pdf_bytes = create_pdf(ticker_input, response.text)
            st.download_button(
                label="📥 Download Full Report (PDF)",
                data=pdf_bytes,
                file_name=f"IsewaInvest_Report_{ticker_input}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with colB:
            with st.expander("⚖️ Important Information & Research Disclaimer"):
                st.markdown(DISCLAIMER_TEXT)

    except Exception as e:
      st.error(f"Execution Error: {str(e)}")

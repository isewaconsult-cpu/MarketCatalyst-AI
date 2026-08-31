import os
import streamlit as st
import yfinance as yf
from google import genai

GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")
).strip()

DISCLAIMER_TEXT = """
### Important Information & Research Disclaimer
**Research for informational and educational purposes only — not personalised investment advice.**

This IsewaInvest report has been prepared by Isewa Investment (IsewaInvest) using publicly available information, historical market data, financial information, market trends, macroeconomic conditions, company-specific factors, valuation metrics and other sources considered relevant at the time of preparation.

The report is intended to provide independent research and analytical information and does not take into account any individual investor's financial situation, investment objectives, knowledge, experience, risk tolerance, investment horizon or capacity for loss.

Nothing contained in this report constitutes personalised investment advice, financial advice, a personal recommendation, an offer, solicitation or invitation to buy, sell or hold any financial instrument.

---

#### Analysis, Estimates & Price Scenarios
Any forecasts, estimates, valuations, price targets, Bull/Base/Bear scenarios, expected returns, projections or opinions presented in this report are analytical estimates and scenarios, not predictions or guarantees. Such estimates are based on assumptions that may change materially. Actual results and market prices may differ substantially from the scenarios presented. **Past performance is not a reliable indicator of future performance.**

#### Investment Risk
Investing in financial markets involves risk. The value of investments may rise or fall, and investors may lose part or all of their invested capital. Market prices can be affected by interest rates, inflation, economic conditions, company performance, earnings expectations, liquidity, currency movements, geopolitical events, regulation, taxation and investor sentiment. **Investors should not invest money they cannot afford to lose.**

#### Independent Due Diligence
**Do your own research before making any investment decision.** Readers should independently verify the latest financial statements, company announcements, regulatory filings, valuation data, market conditions and other relevant information before acting on any information contained in this report. Where appropriate, seek advice from an authorized financial, investment or tax professional.

#### Sources & Data
IsewaInvest seeks to use reliable and publicly available sources. However, third-party data and public filings may contain errors, omissions, delays or subsequent revisions. AI-assisted analysis may be used in the preparation of reports; AI-generated interpretations and estimates should be independently verified against authoritative primary sources.

#### Conflicts of Interest
Isewa Investment will disclose any material interest or known conflict of interest relating to a financial instrument or issuer where required by applicable law or regulation. Readers should not assume that the absence of a disclosure means that no potential conflict exists.

#### Regulatory & Market-Conduct Notice
IsewaInvest research is presented objectively and transparently in accordance with relevant Norwegian and EEA requirements, including the Market Abuse Regulation (MAR) and applicable rules concerning investment recommendations.

---
**Final Reminder:** *Research informs. You decide.*  
**IsewaInvest** — Independent Equity Research & Market Intelligence.
"""

st.set_page_config(
    page_title="IsewaInvest | Equity Research Terminal",
    page_icon="🏛️",
    layout="wide",
)

st.title("🏛️ IsewaInvest: Equity Research Terminal")
st.markdown(
    "Enter an equity ticker below (use `.OL` for Oslo Børs, e.g., `EQNR.OL`,"
    " `KOG.OL`, `VAR.OL`, `AKRBP.OL`, `NVDA`, `TSLA`)."
)

col1, col2 = st.columns([3, 1])
with col1:
  ticker_input = (
      st.text_input(
          "Enter Ticker Symbol:",
          placeholder="e.g., EQNR.OL, KOG.OL, NVDA, TSLA",
      )
      .strip()
      .upper()
  )

with col2:
  st.write("")
  st.write("")
  run_btn = st.button("Generate Intelligence Report", use_container_width=True)

if run_btn and ticker_input:
  with st.spinner(
      f"Ingesting live telemetry & synthesizing research for {ticker_input}..."
  ):
    try:
      # 1. Ingest Market Telemetry
      stock = yf.Ticker(ticker_input)
      info = stock.info or {}
      hist = stock.history(period="1y")

      if hist.empty:
        st.error(f"No price history found for ticker: {ticker_input}")
      else:
        curr_price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or hist["Close"].iloc[-1]
        )
        currency = info.get(
            "currency", "NOK" if ticker_input.endswith(".OL") else "USD"
        )
        forward_pe = info.get("forwardPE", "N/A")
        trailing_pe = info.get("trailingPE", "N/A")
        div_yield = (
            f"{info.get('dividendYield', 0) * 100:.2f}%"
            if info.get("dividendYield")
            else "N/A"
        )
        high_52 = info.get(
            "fiftyTwoWeekHigh", round(float(hist["Close"].max()), 2)
        )
        low_52 = info.get(
            "fiftyTwoWeekLow", round(float(hist["Close"].min()), 2)
        )
        sma_200 = (
            round(float(hist["Close"].rolling(200).mean().iloc[-1]), 2)
            if len(hist) >= 200
            else "N/A"
        )
        target_mean = info.get("targetMeanPrice", "N/A")
        recommendation_key = info.get("recommendationKey", "N/A").upper()

        market_context = f"""
                Ticker: {ticker_input}
                Company: {info.get('longName', ticker_input)}
                Sector: {info.get('sector', 'N/A')} | Industry: {info.get('industry', 'N/A')}
                Current Price: {curr_price} {currency}
                52-Week Range: {low_52} - {high_52} {currency}
                200-Day Moving Average: {sma_200} {currency}
                Trailing P/E: {trailing_pe} | Forward P/E: {forward_pe}
                Dividend Yield: {div_yield}
                Consensus Recommendation: {recommendation_key} | Mean Target: {target_mean} {currency}
                Market Cap: {info.get('marketCap', 'N/A')} {currency}
                """

        # 2. Institutional Synthesis via Gemini
        client = genai.Client(api_key=GEMINI_API_KEY)
        system_prompt = """
                You are MarketCatalyst AI, an elite Equity Research Analyst covering US markets (S&P 500, NASDAQ) and Norwegian markets (Oslo Børs / OSEBX).
                Structure your evaluation strictly using the following 5 institutional modules:

                ### 1. Market Catalyst & Newsflash Classification
                - Tag with: [Earnings / Guidance], [Capital Allocation], [Regulatory & Contracts], or [Macro / Commodity Trigger].
                - Summarize core catalysts and expectation gaps.

                ### 2. Institutional Consensus & Valuation Bias
                - Provide visual bias tag (🟢 OVERWEIGHT / BUY BIAS, 🟡 NEUTRAL / HOLD BIAS, or 🔴 UNDERWEIGHT / REDUCE BIAS).
                - Consensus Barometer: Target price spread and analyst profile.

                ### 3. High-Signal Quantitative Metrics
                - Earnings Revision Momentum (30/90 day trends).
                - Multiples vs. 5-Year Medians (NTM P/E, EV/EBITDA, P/FCF).
                - Balance sheet leverage (Net Debt / EBITDA, Interest Coverage).
                - Macro & FX Sensitivity (Brent delta for OSEBX; DXY / 10Y Yields for US).

                ### 4. Corporate Actions, Dividend & Dilution Analytics
                - Dividend CAGR (3/5/10 yr) & FCF Payout Coverage.
                - Payout structure (Nordic base + extraordinary vs. US quarterly).
                - 5-year share count / net dilution trajectory.

                ### 5. Primary Source & Verification Box
                - Structured markdown table citing regulatory filings (SEC EDGAR vs. Euronext Oslo Newsweb), IR portals, and earnings transcripts.

                Strictly distinguish between USD and NOK. Jump directly into the analysis without introductory conversational filler.
                """

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[system_prompt, market_context],
        )

        st.success(f"Report Generated: {info.get('longName', ticker_input)}")
        st.markdown("---")
        st.markdown(response.text)

        # Institutional Compliance & Legal Disclaimer Scaffolding
        st.markdown("---")
        with st.expander("⚖️ Important Information & Research Disclaimer"):
          st.markdown(DISCLAIMER_TEXT)
          st.download_button(
              label="📥 Download Research Disclaimer (TXT)",
              data=DISCLAIMER_TEXT,
              file_name="IsewaInvest_Research_Disclaimer.txt",
              mime="text/plain",
          )

    except Exception as e:
      st.error(f"Execution Error: {str(e)}")

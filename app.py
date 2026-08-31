import os
import streamlit as st
import yfinance as yf
from google import genai

# Fetch API key from Streamlit Secrets or Environment Variable
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
      # 1. Fetch live market telemetry
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

        market_context = f"""
                Ticker: {ticker_input}
                Company: {info.get('longName', ticker_input)}
                Sector: {info.get('sector', 'N/A')} | Industry: {info.get('industry', 'N/A')}
                Current Price: {curr_price} {currency}
                52-Week Range: {low_52} - {high_52} {currency}
                200-Day Moving Average: {sma_200} {currency}
                Forward P/E: {forward_pe}
                Dividend Yield: {div_yield}
                Market Cap: {info.get('marketCap', 'N/A')} {currency}
                """

        # 2. Institutional Synthesis via Gemini
        client = genai.Client(api_key=GEMINI_API_KEY)
        system_prompt = """
                You are IsewaInvest AI, an elite Equity Research Analyst covering US markets (S&P 500, NASDAQ) and Norwegian markets (OSEBX).
                Structure your evaluation strictly using these 5 institutional steps:
                **1. Catalyst Breakdown**
                **2. Historical Context & Price Action**
                **3. Macro & Sector Drivers**
                **4. Fundamental & Dividend Health**
                **5. Scenario Synthesis** (Bull/Bear cases, key risk triggers, and target price levels)
                Distinguish clearly between USD and NOK. Maintain an institutional, concise, and scannable format.
                """

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[system_prompt, market_context],
        )

        st.success(f"Report Generated: {info.get('longName', ticker_input)}")
        st.markdown("---")
        st.markdown(response.text)

    except Exception as e:
      st.error(f"Execution Error: {str(e)}")

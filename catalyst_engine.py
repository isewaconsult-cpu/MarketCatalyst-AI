import os
import requests
import yfinance as yf
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def send_telegram_alert(message: str):
  """Dispatches formatted intelligence reports directly to Telegram."""
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
  }
  response = requests.post(url, json=payload, timeout=15)
  return response.json()


def get_market_quote(ticker_symbol: str) -> dict:
  """Fetches real-time price and percentage change."""
  try:
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="2d")
    if len(hist) >= 2:
      prev_close = hist["Close"].iloc[-2]
      curr_price = hist["Close"].iloc[-1]
      pct_change = ((curr_price - prev_close) / prev_close) * 100
      return {
          "price": round(curr_price, 2),
          "pct": f"{pct_change:+.2f}%",
          "valid": True,
      }
    elif len(hist) == 1:
      return {
          "price": round(hist["Close"].iloc[-1], 2),
          "pct": "0.00%",
          "valid": True,
      }
  except Exception:
    pass
  return {"price": "N/A", "pct": "N/A", "valid": False}


# 1. Market Telemetry Ingestion
# Domestic (Oslo Børs)
eqnr = get_market_quote("EQNR.OL")
kog = get_market_quote("KOG.OL")
var_ol = get_market_quote("VAR.OL")
akrbp = get_market_quote("AKRBP.OL")
usdnok = get_market_quote("USDNOK=X")

# International, Geopolitical & Commodity Telemetry
brent = get_market_quote("BZ=F")
spx = get_market_quote("^GSPC")
asx = get_market_quote("^AXJO")
nikkei = get_market_quote("^N225")
ongc = get_market_quote("ONGC.NS")
reliance = get_market_quote("RELIANCE.NS")
ioc = get_market_quote("IOC.NS")

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

# =======================================================
# MESSAGE 1: OSLOBØRS (Domestic E&P, Defense, FX)
# =======================================================
prompt_oslo = f"""
You are MarketCatalyst AI, an institutional Equity Research Analyst covering Oslo Børs (OSEBX).
Generate an institutional morning/hourly flash report.
The top headline MUST BE: 🏛️ [Oslobørs] Equity & Energy Intelligence

Market Data:
- Brent Spot: ${brent['price']} ({brent['pct']})
- USD/NOK: {usdnok['price']} ({usdnok['pct']})
- EQNR.OL: {eqnr['price']} NOK ({eqnr['pct']}) | AKRBP.OL: {akrbp['price']} NOK ({akrbp['pct']})
- VAR.OL: {var_ol['price']} NOK ({var_ol['pct']}) | KOG.OL: {kog['price']} NOK ({kog['pct']})

Apply the 5-step framework concisely:
* **Catalyst & Price Action:** Core moves across offshore E&P and Kongsberg Gruppen backlog momentum.
* **Macro & FX Drivers:** Brent crude spot resilience on FCF yields and USD/NOK translation dynamics.
* **Fundamental & Balance Sheet:** Dividend safety metrics and capital expenditure discipline.
* **Actionable Watchpoints:** Key technical support/resistance bands.

Strict limit: 220 words. Use crisp bullet points and clear bold headings.
"""

response_oslo = client.models.generate_content(
    model="gemini-3.6-flash", contents=[prompt_oslo]
)

# =======================================================
# MESSAGE 2: ISEWAINTERNATIONAL (US, APAC & India Energy)
# =======================================================
prompt_intl = f"""
You are MarketCatalyst AI, an institutional Equity Research Analyst covering Global Markets.
Generate an institutional geopolitical and multi-market flash report.
The top headline MUST BE: 🌐 [IsewaInternational] US, APAC & Geopolitical Energy Flash

Market Data:
- S&P 500: {spx['price']} ({spx['pct']})
- Brent Spot: ${brent['price']} ({brent['pct']})
- Australia (ASX 200): {asx['price']} ({asx['pct']})
- Japan (Nikkei 225): {nikkei['price']} ({nikkei['pct']})
- Indian Energy: ONGC ({ongc['price']} INR, {ongc['pct']}), Reliance ({reliance['price']} INR, {reliance['pct']}), IOC ({ioc['price']} INR, {ioc['pct']})

Apply the 5-step framework concisely:
* **US Index & Defense Watch:** S&P 500 momentum, US Treasury yield sensitivity, and defense contractors (Raytheon, Lockheed, Ondas).
* **Geopolitical & Brent Dynamics:** Maritime chokepoints, supply elasticity, and crude price action.
* **APAC & Indian Energy Matrix:**
  - ASX & Nikkei opening/closing tone on raw commodities.
  - Indian downstream vs. upstream dynamics (ONGC crude margin expansion vs. Reliance/IOC refining margins).

Strict limit: 250 words. Use crisp bullet points and clear bold headings.
"""

response_intl = client.models.generate_content(
    model="gemini-3.6-flash", contents=[prompt_intl]
)

# Dispatch two distinct messages to Telegram
send_telegram_alert(response_oslo.text)
send_telegram_alert(response_intl.text)
print(
    "[+] Successfully executed dual dispatch: [Oslobørs] and"
    " [IsewaInternational]"
)

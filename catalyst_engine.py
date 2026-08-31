import os
import sys
import requests
import yfinance as yf
from google import genai

# Ingest Environment Variables / Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Verification check
if not GEMINI_API_KEY:
  print("[-] Error: GEMINI_API_KEY secret is missing.")
  sys.exit(1)
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
  print("[-] Error: Telegram secrets are missing.")
  sys.exit(1)

# Institutional Compliance & Disclaimer Footer
DISCLAIMER_FOOTER = (
    "\n\n---\n"
    "⚖️ [Important Information & Research"
    " Disclaimer](https://isewainvest.streamlit.app)\n"
    "_Research for informational & educational purposes only — not personalized"
    " investment advice._"
)


def send_telegram_alert(message: str):
  """Dispatches message to Telegram with Markdown fallback to plain text."""
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
      "disable_web_page_preview": True,
  }
  res = requests.post(url, json=payload, timeout=20)
  if res.status_code != 200:
    print(
        f"[!] Telegram Markdown dispatch warning ({res.status_code}). Retrying"
        " as plain text..."
    )
    payload.pop("parse_mode")
    res = requests.post(url, json=payload, timeout=20)
  return res.json()


def get_market_quote(ticker_symbol: str) -> dict:
  """Safely retrieves market telemetry."""
  try:
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="2d")
    if len(hist) >= 2:
      prev = hist["Close"].iloc[-2]
      curr = hist["Close"].iloc[-1]
      pct = ((curr - prev) / prev) * 100
      return {"price": round(curr, 2), "pct": f"{pct:+.2f}%"}
    elif len(hist) == 1:
      return {"price": round(hist["Close"].iloc[-1], 2), "pct": "0.00%"}
  except Exception as e:
    print(f"[!] Warning fetching {ticker_symbol}: {e}")
  return {"price": "N/A", "pct": "N/A"}


def generate_synthesis(client, prompt: str) -> str:
  """Executes synthesis with dynamic model fallback."""
  for model_id in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]:
    try:
      response = client.models.generate_content(
          model=model_id, contents=[prompt]
      )
      if response.text:
        return response.text
    except Exception as err:
      print(f"[!] Model {model_id} failed: {err}. Trying fallback...")
  raise RuntimeError("All Gemini model endpoints failed.")


print("[+] Ingesting live market telemetry...")
# Oslo Børs Telemetry
eqnr = get_market_quote("EQNR.OL")
kog = get_market_quote("KOG.OL")
var_ol = get_market_quote("VAR.OL")
akrbp = get_market_quote("AKRBP.OL")
usdnok = get_market_quote("USDNOK=X")

# Global & Commodity Telemetry
brent = get_market_quote("BZ=F")
spx = get_market_quote("^GSPC")
asx = get_market_quote("^AXJO")
nikkei = get_market_quote("^N225")
ongc = get_market_quote("ONGC.NS")
reliance = get_market_quote("RELIANCE.NS")
ioc = get_market_quote("IOC.NS")

client = genai.Client(api_key=GEMINI_API_KEY)

# =========================================================
# MESSAGE 1: OSLOBØRS (Norway Domestic, E&P, Defense, FX)
# =========================================================
prompt_oslo = f"""
You are MarketCatalyst AI, an elite Equity Research Analyst covering Oslo Børs (OSEBX).
Generate an institutional morning/hourly intelligence flash.
The top headline MUST BE: 🏛️ [Oslobørs] Equity & Energy Intelligence

Market Data:
- Brent Crude Spot: ${brent['price']} ({brent['pct']})
- USD/NOK FX: {usdnok['price']} ({usdnok['pct']})
- EQNR.OL: {eqnr['price']} NOK ({eqnr['pct']}) | AKRBP.OL: {akrbp['price']} NOK ({akrbp['pct']})
- VAR.OL: {var_ol['price']} NOK ({var_ol['pct']}) | KOG.OL: {kog['price']} NOK ({kog['pct']})

Structure:
* **Catalyst & Price Action:** Core moves across offshore E&P and Kongsberg Gruppen defense backlog.
* **Macro & FX Drivers:** Brent crude spot impact on FCF yields and USD/NOK currency translation.
* **Fundamental & Balance Sheet:** Dividend coverage metrics and capex discipline.
* **Actionable Watchpoints:** Key technical levels for KOG.OL and EQNR.OL.

Strict limit: 200 words. Format with clean bullet points and bold headers.
"""

print("[+] Synthesizing Oslobørs report...")
report_oslo = generate_synthesis(client, prompt_oslo)
full_oslo_message = report_oslo.strip() + DISCLAIMER_FOOTER
send_telegram_alert(full_oslo_message)
print("[+] Message 1 ([Oslobørs]) with compliance footer dispatched.")

# =========================================================
# MESSAGE 2: ISEWAINTERNATIONAL (US, APAC & India Energy)
# =========================================================
prompt_intl = f"""
You are MarketCatalyst AI, an elite Equity Research Analyst covering Global Markets.
Generate an institutional geopolitical and multi-market flash.
The top headline MUST BE: 🌐 [IsewaInternational] US, APAC & Geopolitical Energy Flash

Market Data:
- S&P 500: {spx['price']} ({spx['pct']})
- Brent Spot: ${brent['price']} ({brent['pct']})
- Australia (ASX 200): {asx['price']} ({asx['pct']})
- Japan (Nikkei 225): {nikkei['price']} ({nikkei['pct']})
- Indian Energy: ONGC ({ongc['price']} INR, {ongc['pct']}), Reliance ({reliance['price']} INR, {reliance['pct']}), IOC ({ioc['price']} INR, {ioc['pct']})

Structure:
* **US Index & Defense Watch:** S&P 500 momentum, US Treasury yield sensitivity, and defense pipeline (Raytheon, Lockheed, Ondas).
* **Geopolitical & Brent Dynamics:** Maritime bottlenecks, supply elasticity, and crude price action.
* **APAC & Indian Energy Matrix:**
  - ASX & Nikkei opening/closing tone on raw energy commodities.
  - Indian downstream vs. upstream dynamics (ONGC upstream crude margin expansion vs. Reliance/IOC refining margins).

Strict limit: 220 words. Format with clean bullet points and bold headers.
"""

print("[+] Synthesizing IsewaInternational report...")
report_intl = generate_synthesis(client, prompt_intl)
full_intl_message = report_intl.strip() + DISCLAIMER_FOOTER
send_telegram_alert(full_intl_message)
print(
    "[+] Message 2 ([IsewaInternational]) with compliance footer dispatched."
)

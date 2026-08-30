import os
import json
import re
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from google import genai

# 1. Retrieve Secrets from GitHub Environment
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8857375031").strip()

if not GEMINI_KEY:
    raise ValueError("Missing GEMINI_API_KEY repository secret.")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN repository secret.")

# 2. Institutional Portfolio & Watchlist
PORTFOLIO_HOLDINGS = [
    {
        "ticker": "EQNR.OL",
        "name": "Equinor ASA",
        "market": "OSEBX",
        "currency": "NOK",
        "shares": 100,
        "avg_buy_price": 280.0,
        "target_price": 340.0,
        "stop_loss_price": 255.0,
        "thesis": "High FCF yield, sustained European gas demand, solid dividend profile."
    },
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "market": "US",
        "currency": "USD",
        "shares": 15,
        "avg_buy_price": 115.0,
        "target_price": 160.0,
        "stop_loss_price": 100.0,
        "thesis": "Data center compute demand, AI infrastructure capital expenditure cycle."
    }
]

WATCHLIST_TARGETS = [
    {
        "ticker": "DNB.OL",
        "name": "DNB Bank ASA",
        "market": "OSEBX",
        "currency": "NOK",
        "target_entry_price": 210.0,
        "catalyst_to_watch": "Norges Bank rate pathway, net interest margin sustainability."
    },
    {
        "ticker": "MSFT",
        "name": "Microsoft Corporation",
        "market": "US",
        "currency": "USD",
        "target_entry_price": 410.0,
        "catalyst_to_watch": "Azure growth acceleration, commercial cloud margin expansion."
    }
]

def calculate_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 2) if not np.isnan(rsi.iloc[-1]) else 50.0

def fetch_macro_benchmarks() -> dict:
    benchmarks = {
        "BRENT_CRUDE_USD": "BZ=F",
        "USD_NOK": "USDNOK=X",
        "EUR_NOK": "EURNOK=X",
        "US_10Y_YIELD_PCT": "^TNX"
    }
    data = {}
    for name, ticker in benchmarks.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if not hist.empty:
                curr = round(float(hist['Close'].iloc[-1]), 2)
                prev = round(float(hist['Close'].iloc[-2]), 2)
                chg = round(((curr - prev) / prev) * 100, 2)
                data[name] = {"current": curr, "change_pct_1d": chg}
        except Exception:
            data[name] = {"current": "N/A", "change_pct_1d": 0.0}
    return data

def analyze_ticker(ticker_symbol: str) -> dict:
    try:
        t = yf.Ticker(ticker_symbol)
        hist = t.history(period="1y")
        if hist.empty:
            return {"ticker": ticker_symbol, "error": "No price data"}

        close = hist['Close']
        curr = round(float(close.iloc[-1]), 2)
        prev = round(float(close.iloc[-2]), 2)
        day_chg = round(((curr - prev) / prev) * 100, 2)
        rsi = calculate_rsi(close)
        sma_200 = round(float(close.rolling(window=200).mean().iloc[-1]), 2) if len(close) >= 200 else curr

        info = t.info or {}
        return {
            "ticker": ticker_symbol,
            "current_price": curr,
            "day_change_pct": day_chg,
            "rsi_14": rsi,
            "above_200_dma": bool(curr > sma_200),
            "pe_forward": info.get('forwardPE', None),
            "dividend_yield_pct": round(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else 0.0
        }
    except Exception as e:
        return {"ticker": ticker_symbol, "error": str(e)}

def run_pipeline():
    print("[*] Ingesting macro barometers...")
    macro_data = fetch_macro_benchmarks()

    print("[*] Fetching equity metrics...")
    portfolio_metrics = [analyze_ticker(item['ticker']) for item in PORTFOLIO_HOLDINGS]
    watchlist_metrics = [analyze_ticker(item['ticker']) for item in WATCHLIST_TARGETS]

    client = genai.Client(api_key=GEMINI_KEY)

    prompt = f"""
You are MarketCatalyst AI, an elite Equity Research Analyst covering US (S&P 500/NASDAQ) and Norwegian (OSEBX) equities.
Evaluate the current market snapshot and generate structured signals.

Macro: {json.dumps(macro_data)}
Portfolio: {json.dumps(portfolio_metrics)}
Watchlist: {json.dumps(watchlist_metrics)}

Output strictly valid JSON with this exact structure:
{{
  "macro_regime_summary": "Concise 1-2 sentence macro status",
  "portfolio_signals": [
    {{
      "ticker": "TICKER",
      "signal": "STRONG ACCUMULATE | HOLD / MAINTAIN | TRIM / REDUCE | FULL EXIT",
      "conviction_score": 0.00,
      "catalyst_breakdown": "Driver breakdown",
      "actionable_trigger": "Key threshold"
    }}
  ],
  "watchlist_signals": [
    {{
      "ticker": "TICKER",
      "signal": "INITIATE BUY | SCALE-IN | MONITOR / WAIT | PASS",
      "conviction_score": 0.00,
      "catalyst_breakdown": "Entry rationale",
      "actionable_trigger": "Price/catalyst trigger"
    }}
  ]
}}
"""

    print("[*] Synthesizing signals via Gemini...")
    candidate_models = ["gemini-3.6-flash", "gemini-2.0-flash", "gemini-2.5-pro"]
    response = None

    for model_name in candidate_models:
        try:
            print(f"[*] Querying model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                print(f"[+] Connected to {model_name}")
                break
        except Exception as e:
            print(f"[-] {model_name} skipped: {e}")

    if not response or not response.text:
        raise RuntimeError("Failed to generate signals from all Gemini model endpoints.")

    raw = response.text.strip()
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    signals = json.loads(match.group(0)) if match else json.loads(raw)

    # Format Telegram Card
    brent = macro_data.get("BRENT_CRUDE_USD", {}).get("current", "N/A")
    brent_chg = macro_data.get("BRENT_CRUDE_USD", {}).get("change_pct_1d", 0)
    usdnok = macro_data.get("USD_NOK", {}).get("current", "N/A")
    yield_10y = macro_data.get("US_10Y_YIELD_PCT", {}).get("current", "N/A")

    msg = "🏛 <b>MarketCatalyst AI | Automated Cloud Dispatch</b>\n"
    msg += f"📊 <i>Macro: Brent ${brent} ({brent_chg:+.1f}%) | USD/NOK {usdnok} | US 10Y {yield_10y}%</i>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"🌐 <b>Macro Regime:</b>\n{signals.get('macro_regime_summary', 'N/A')}\n\n"

    msg += "💼 <b>PORTFOLIO HOLDINGS:</b>\n"
    for item in signals.get('portfolio_signals', []):
        sig = item.get('signal', '')
        icon = "🟢" if "ACCUMULATE" in sig else ("🔴" if "TRIM" in sig or "EXIT" in sig else "🟡")
        msg += f"{icon} <b>{item.get('ticker')}</b>: <code>{sig}</code> (Score: {item.get('conviction_score', 0):+.2f})\n"
        msg += f"• <b>Driver:</b> {item.get('catalyst_breakdown', 'N/A')}\n"
        msg += f"• <b>Action:</b> {item.get('actionable_trigger', 'N/A')}\n\n"

    msg += "🎯 <b>WATCHLIST TARGETS:</b>\n"
    for item in signals.get('watchlist_signals', []):
        sig = item.get('signal', '')
        icon = "🔵" if "BUY" in sig or "SCALE" in sig else "⚪"
        msg += f"{icon} <b>{item.get('ticker')}</b>: <code>{sig}</code> (Score: {item.get('conviction_score', 0):+.2f})\n"
        msg += f"• <b>Setup:</b> {item.get('catalyst_breakdown', 'N/A')}\n"
        msg += f"• <b>Trigger:</b> {item.get('actionable_trigger', 'N/A')}\n\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n⚡ <i>MarketCatalyst AI Cloud Runner</i>"

    res = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    )
    if res.status_code == 200:
        print("[+] Automated dispatch successfully delivered to Telegram.")
    else:
        print(f"[!] Telegram delivery failed ({res.status_code}): {res.text}")

if __name__ == '__main__':
    run_pipeline()

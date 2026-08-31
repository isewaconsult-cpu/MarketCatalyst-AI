import os
import streamlit as st
from google import genai
from google.genai import types
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="MarketCatalyst AI | Equity Research Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
        .main { background-color: #0b0f19; color: #f3f4f6; }
        .stMetric { background-color: #161e2e; border: 1px solid #233044; padding: 12px; border-radius: 6px; }
        .badge-pro { background-color: #059669; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }
        .badge-free { background-color: #4b5563; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. LOCAL USER STORE & GEMINI CLIENT
# ---------------------------------------------------------
if "users_db" not in st.session_state:
    # Default master account
    st.session_state.users_db = {
        "preetam@isewa.no": {"name": "Preetam Pandey", "password": "!Pre3t4m2020", "tier": "institutional"}
    }

if "logged_user" not in st.session_state:
    st.session_state.logged_user = None

def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
    return genai.Client(api_key=api_key)

# ---------------------------------------------------------
# 3. AUTHENTICATION SCREENS
# ---------------------------------------------------------
def auth_screen():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.title("⚡ MarketCatalyst AI")
        st.caption("Event-Driven Equity Research & Global Market Intelligence")
        
        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email").strip().lower()
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign in", use_container_width=True)
                
                if submit:
                    user_data = st.session_state.users_db.get(email)
                    if user_data and user_data["password"] == password:
                        st.session_state.logged_user = {
                            "email": email,
                            "name": user_data["name"],
                            "tier": user_data["tier"]
                        }
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

        with tab_signup:
            with st.form("signup_form"):
                su_name = st.text_input("Full Name").strip()
                su_email = st.text_input("Email").strip().lower()
                su_password = st.text_input("Password", type="password")
                su_submit = st.form_submit_button("Create Account", use_container_width=True)
                
                if su_submit:
                    if not su_email or not su_password:
                        st.warning("Please fill in all fields.")
                    elif su_email in st.session_state.users_db:
                        st.error("Account already exists with this email.")
                    else:
                        st.session_state.users_db[su_email] = {
                            "name": su_name,
                            "password": su_password,
                            "tier": "pro"
                        }
                        st.success("Account created successfully. Switch to 'Sign In' to enter.")

# ---------------------------------------------------------
# 4. CORE TERMINAL INTERFACE
# ---------------------------------------------------------
def render_terminal():
    user = st.session_state.logged_user
    tier = user.get("tier", "pro")
    
    with st.sidebar:
        st.markdown(f"**Operator:** `{user['email']}`")
        st.markdown(f"**Name:** `{user['name']}`")
        badge_class = "badge-pro" if tier in ["pro", "institutional"] else "badge-free"
        st.markdown(f"Tier: <span class='{badge_class}'>{tier.upper()}</span>", unsafe_allow_html=True)
        st.markdown("---")
        
        market_universe = st.radio(
            "Primary Market", 
            ["US Equities (S&P 500 / NASDAQ / NYSE)", "Norwegian Equities (OSEBX / Euronext)"]
        )
        default_ticker = "NVDA" if "US" in market_universe else "EQNR.OL"
        ticker = st.text_input("Ticker Symbol", value=default_ticker).upper().strip()
        timeframe = st.selectbox("Historical Benchmark Window", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
        
        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.logged_user = None
            st.rerun()

    st.subheader(f"⚡ Financial Intelligence Console: {ticker}")
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=timeframe)
        info = stock.info
        
        if hist.empty:
            st.warning(f"No market data located for `{ticker}`. Verify ticker suffix (e.g., `.OL` for Oslo Børs).")
            return

        c1, c2, c3, c4 = st.columns(4)
        currency = info.get("currency", "USD")
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        pct_change = ((current_price - prev_close) / prev_close) * 100
        
        c1.metric(label=f"Price ({currency})", value=f"{current_price:,.2f}", delta=f"{pct_change:+.2f}%")
        c2.metric(label="Market Cap", value=f"{info.get('marketCap', 0):,}")
        c3.metric(label="Trailing P/E", value=f"{info.get('trailingPE', 'N/A')}")
        div_yield = info.get('dividendYield')
        c4.metric(label="Dividend Yield", value=f"{div_yield*100:.2f}%" if div_yield else "N/A")

        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name=ticker
        )])
        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=400,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📋 Institutional Catalyst Breakdown & Macro Synthesis")
        analysis_prompt = st.text_area(
            "Event Trigger / Analysis Context", 
            value=f"Evaluate recent quarterly earnings, monetary policy posture (Fed / Norges Bank), and balance sheet durability for {ticker}."
        )

        if st.button("Generate Catalyst Analysis", type="primary"):
            with st.spinner("Synthesizing multi-source financial telemetry..."):
                client = get_gemini_client()
                
                system_instruction = """
You are MarketCatalyst AI, an elite Equity Research Analyst and Financial Intelligence Specialist. Your domain expertise covers both US financial markets (S&P 500, NASDAQ, NYSE) and Norwegian markets (Oslo Børs / OSEBX). You specialize in event-driven financial analysis, correlating historical price behavior with news releases, leadership statements, corporate filings, and macroeconomic developments.

Key Analytical Framework:
1. Catalyst Breakdown: Identify the core event (e.g., quarterly earnings release, executive guidance, interest rate decision, regulatory flash, or dividend announcement).
2. Historical Context & Price Action: Compare current price reactions against historical event precedents.
3. Macro & Sector Drivers:
   - For US stocks: Fed rate path, Treasury yields, US CPI/PCE data, sector rotation.
   - For Norwegian stocks: Norges Bank policy rates, Brent crude pricing, USD/NOK and EUR/NOK currency dynamics, European power markets.
4. Fundamental & Dividend Health: Review revenue/EPS trends, balance sheet strength, dividend sustainability, and payout coverage.
5. Scenario Synthesis: Formulate clear Bull/Bear pathways, risk factors, and upcoming catalyst dates.

Format with bold headers, concise bullet points, and scannable financial tables. Maintain institutional rigor and objectivity. Provide market intelligence without personalized investment advice.
"""

                prompt = f"""
Analyze the following security and event context according to the 5-step Analytical Framework:
- Security: {ticker} ({info.get('longName', ticker)})
- Sector / Industry: {info.get('sector', 'N/A')} / {info.get('industry', 'N/A')}
- Market Universe: {market_universe}
- Current Reference Price: {current_price:.2f} {currency}
- Trailing P/E: {info.get('trailingPE', 'N/A')}
- User Context / Target Trigger: {analysis_prompt}
"""

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    ),
                )
                
                st.markdown("---")
                st.markdown(response.text)

    except Exception as e:
        st.error(f"Error compiling equity telemetry: {str(e)}")

# ---------------------------------------------------------
# 5. EXECUTION ROUTER
# ---------------------------------------------------------
if st.session_state.logged_user is None:
    auth_screen()
else:
    render_terminal()

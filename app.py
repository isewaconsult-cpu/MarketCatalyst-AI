import os
import streamlit as st
from supabase import create_client, Client
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
# 2. CLIENT INITIALIZATION
# ---------------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
    return genai.Client(api_key=api_key)

# ---------------------------------------------------------
# 3. AUTHENTICATION HANDLERS
# ---------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "profile" not in st.session_state:
    st.session_state.profile = None

def fetch_profile(user_id):
    res = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if res.data:
        return res.data[0]
    return None

def auth_screen():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.title("⚡ MarketCatalyst AI")
        st.caption("Event-Driven Equity Research & Global Market Intelligence")
        
        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign in", use_container_width=True)
                
                if submit:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user
                        st.session_state.profile = fetch_profile(res.user.id)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Authentication Failed: {str(e)}")

        with tab_signup:
            with st.form("signup_form"):
                su_name = st.text_input("Full Name")
                su_email = st.text_input("Email")
                su_password = st.text_input("Password", type="password")
                su_submit = st.form_submit_button("Create Account", use_container_width=True)
                
                if su_submit:
                    try:
                        res = supabase.auth.sign_up({
                            "email": su_email,
                            "password": su_password,
                            "options": {"data": {"full_name": su_name}}
                        })
                        st.success("Account created successfully. Please switch to the Sign In tab to enter.")
                    except Exception as e:
                        st.error(f"Registration Failed: {str(e)}")

# ---------------------------------------------------------
# 4. CORE TERMINAL INTERFACE
# ---------------------------------------------------------
def render_terminal():
    user = st.session_state.user
    profile = st.session_state.profile
    tier = profile.get("subscription_tier", "free") if profile else "free"
    
    with st.sidebar:
        st.markdown(f"**Operator:** `{user.email}`")
        badge_class = "badge-pro" if tier in ["pro", "institutional"] else "badge-free"
        st.markdown(f"Tier: <span class='{badge_class}'>{tier.upper()}</span>", unsafe_allow_html=True)
        st.markdown("---")
        
        market_universe = st.radio("Primary Market", ["US Equities (S&P 500 / NASDAQ)", "Norwegian Equities (OSEBX / Euronext)"])
        default_ticker = "NVDA" if "US" in market_universe else "EQNR.OL"
        ticker = st.text_input("Ticker Symbol", value=default_ticker).upper().strip()
        timeframe = st.selectbox("Historical Benchmark Window", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
        
        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.profile = None
            st.rerun()

    st.subheader(f"⚡ Financial Intelligence Console: {ticker}")
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=timeframe)
        info = stock.info
        
        if hist.empty:
            st.warning(f"No market series located for symbol `{ticker}`. Verify ticker suffix (e.g., `.OL` for Oslo Børs).")
            return

        c1, c2, c3, c4 = st.columns(4)
        currency = info.get("currency", "USD")
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        pct_change = ((current_price - prev_close) / prev_close) * 100
        
        c1.metric(label=f"Price ({currency})", value=f"{current_price:,.2f}", delta=f"{pct_change:+.2f}%")
        c2.metric(label="Market Cap", value=f"{info.get('marketCap', 0):,}")
        c3.metric(label="Trailing P/E", value=f"{info.get('trailingPE', 'N/A')}")
        c4.metric(label="Dividend Yield", value=f"{(info.get('dividendYield') or 0)*100:.2f}%" if info.get('dividendYield') else "N/A")

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
            "Event Trigger / Context Input", 
            value=f"Evaluate recent earnings disclosures, macro conditions (Fed/Norges Bank policy rates), and margin durability for {ticker}."
        )

        if st.button("Generate Catalyst Analysis", type="primary"):
            with st.spinner("Synthesizing multi-source intelligence..."):
                client = get_gemini_client()
                
                system_instruction = (
                    "You are MarketCatalyst AI, an elite Equity Research Analyst specializing in US and Norwegian equities. "
                    "Analyze events systematically using: 1. Catalyst Breakdown, 2. Historical Context & Price Action, "
                    "3. Macro & Sector Drivers (Fed/Norges Bank, rates, FX USD/NOK, Brent oil), "
                    "4. Fundamental & Dividend Health, 5. Scenario Synthesis (Bull/Bear & Watchpoints). "
                    "Use precise, institutional terminology, avoid sensationalism, and format with bold headers and scannable bullet points."
                )

                prompt = f"""
                Analyze the following security and event context:
                - Security: {ticker} ({info.get('longName', ticker)})
                - Sector/Industry: {info.get('sector', 'N/A')} / {info.get('industry', 'N/A')}
                - Market: {market_universe}
                - Recent Close: {current_price:.2f} {currency}
                - Analysis Objective: {analysis_prompt}
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
if st.session_state.user is None:
    auth_screen()
else:
    render_terminal()

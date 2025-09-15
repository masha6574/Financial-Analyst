# app.py

import streamlit as st
import requests
import time
import os
import markdown

# --- Page Configuration ---
st.set_page_config(
    page_title="Financial Analyst AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Custom CSS (omitted for brevity, remains the same as your provided code) ---
st.markdown(
    """
<style>
    /* ... Your existing CSS goes here ... */
    /* --- Keyframe Animations --- */
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    /* --- Global Resets & Font --- */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    /* --- Main App Background & Theme --- */
    .stApp { background-color: #0D0E18; background-image: radial-gradient(ellipse 80% 60% at 50% 110%, rgba(169, 57, 133, 0.5), rgba(224, 73, 73, 0.4), rgba(13, 14, 24, 0)); background-attachment: fixed; color: #ffffff; }
    .main .block-container { padding: 0; }
    /* --- Column Styling --- */
    div[data-testid="column"] { height: 100vh; }
    /* Left Column (Inputs) */
    div[data-testid="column"]:nth-of-type(1) { padding: 2.5rem; display: flex; flex-direction: column; justify-content: center; }
    /* Right Column (Canvas) */
    div[data-testid="column"]:nth-of-type(2) { border-left: 1px solid #2D2E3F; display: flex; align-items: center; justify-content: center; padding: 2.5rem; }
    /* --- Input Section Container --- */
    .input-container { background: rgba(30, 31, 42, 0.7); border: 1px solid #2D2E3F; border-radius: 18px; padding: 2.5rem; backdrop-filter: blur(15px); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); }
    /* --- Header Section --- */
    .main-title { font-size: 2.5rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.75rem; }
    .subtitle { font-size: 1rem; color: #a0aec0; font-weight: 400; line-height: 1.5; margin-bottom: 2.5rem; }
    /* --- Input Fields Styling --- */
    .stTextInput label, .stTextArea label { color: #cbd5e0 !important; font-weight: 500 !important; font-size: 0.9rem !important; margin-bottom: 8px !important; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea { background-color: rgba(13, 14, 24, 0.8) !important; border: 1px solid #3a3b4d !important; border-radius: 10px !important; color: #ffffff !important; padding: 1rem !important; transition: all 0.2s ease-in-out !important; }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: #8A55F7 !important; box-shadow: 0 0 0 3px rgba(138, 85, 247, 0.3) !important; }
    .stTextArea > div > div > textarea { min-height: 120px; resize: none !important; /* Disables resizing */ }
    /* --- Button Styling --- */
    .stButton > button { background: linear-gradient(90deg, #A93985, #E04949) !important; color: white !important; border: none !important; border-radius: 10px !important; padding: 0.9rem !important; font-weight: 600 !important; font-size: 1rem !important; width: 100% !important; transition: transform 0.2s ease, box-shadow 0.2s ease !important; margin-top: 1.5rem !important; box-shadow: 0 4px 20px rgba(224, 73, 73, 0.3) !important; }
    .stButton > button:hover { transform: translateY(-3px) !important; box-shadow: 0 6px 25px rgba(224, 73, 73, 0.4) !important; }
    /* --- Gemini Canvas Styling --- */
    .gemini-canvas { width: 100%; background: transparent; border-radius: 16px; box-shadow: 0 4px 30px rgba(0,0,0,0.4); border: 1px solid rgba(255, 255, 255, 0.15); animation: fadeInUp 0.5s ease-out forwards; max-height: 85vh; overflow-y: auto; }
    .canvas-header { padding: 1.5rem 2rem 1rem 2rem; border-bottom: 1px solid #2D2E3F; }
    .canvas-header h2 { font-size: 1.5rem; color: #FFFFFF; margin: 0; }
    .canvas-body { padding: 1rem 2rem 2rem 2rem; }
    .canvas-body p { line-height: 1.7; color: #D1D5DB; font-size: 1rem; margin-bottom: 1rem; }
    .canvas-body strong { color: #FBBF24; font-weight: 600; }
    .canvas-body ul { list-style-position: outside; padding-left: 1.2rem; }
    .canvas-body li { margin-bottom: 0.5rem; color: #D1D5DB; padding-left: 0.5rem; }
    /* --- Hide Unnecessary Streamlit Elements --- */
    #MainMenu, footer, header, .stDeployButton { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# --- Backend URL Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:7861")

# --- Session State Initialization ---
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
# [NEW] State to manage the manual ticker input field
if "require_manual_ticker" not in st.session_state:
    st.session_state.require_manual_ticker = False
if "stored_query" not in st.session_state:
    st.session_state.stored_query = {}

# --- App Layout (40/60 split) ---
left_column, right_column = st.columns([4, 6])

# --- Left Column (Inputs) ---
with left_column:
    st.markdown(
        '<h1 class="main-title">Financial Analyst AI</h1>', unsafe_allow_html=True
    )
    st.markdown(
        '<p class="subtitle">Your intelligent co-pilot for financial document analysis.</p>',
        unsafe_allow_html=True,
    )

    # [MODIFIED] Store original inputs to pre-fill the form if needed
    company_input_value = st.session_state.stored_query.get("company", "")
    question_input_value = st.session_state.stored_query.get("question", "")

    with st.form(key="input_form"):
        company_input = st.text_input(
            "Company or Ticker",
            placeholder="e.g., Apple Inc. or AAPL",
            value=company_input_value,
        )
        question_input = st.text_area(
            "Your Question",
            placeholder="e.g., Summarize the latest quarterly earnings report...",
            value=question_input_value,
        )

        # [NEW] Conditionally display the manual ticker input
        if st.session_state.require_manual_ticker:
            st.info(
                "Automatic ticker search limit reached. Please provide the exact ticker."
            )
            manual_ticker_input = st.text_input(
                "Exact Stock Ticker", placeholder="e.g., AAPL"
            )
        else:
            manual_ticker_input = None

        analyze_button = st.form_submit_button("Analyze", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if analyze_button:
        if not company_input or not question_input:
            st.warning("Please provide both a company/ticker and a question.")
        else:
            with right_column:
                with st.spinner("AI is analyzing, please wait..."):
                    # [MODIFIED] Build the request body based on whether manual ticker is used
                    request_body = {
                        "company_input": company_input,
                        "question": question_input,
                    }
                    if manual_ticker_input:
                        request_body["exact_ticker"] = manual_ticker_input

                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/query", json=request_body, timeout=600
                        )
                        response.raise_for_status()
                        response_data = response.json()

                        # [MODIFIED] Handle the new API limit status
                        if response_data.get("status") == "api_limit_exceeded":
                            st.session_state.require_manual_ticker = True
                            st.session_state.stored_query = {
                                "company": company_input,
                                "question": question_input,
                            }
                            st.rerun()
                        else:
                            st.session_state.analysis_result = (
                                response_data.get("answer") or "No answer found."
                            )
                            st.session_state.require_manual_ticker = False
                            st.session_state.stored_query = {}

                    except Exception as e:
                        st.session_state.analysis_result = (
                            f"### An Error Occurred\n\n**Details:** `{e}`"
                        )
                        st.session_state.require_manual_ticker = False
                        st.session_state.stored_query = {}
            st.rerun()

# --- Right Column (Canvas Output) ---
with right_column:
    if st.session_state.analysis_result:
        html_content = markdown.markdown(st.session_state.analysis_result)
        canvas_html = f"""
        <div class="gemini-canvas">
            <div class="canvas-header"><h2>Analysis Result</h2></div>
            <div class="canvas-body">{html_content}</div>
        </div>
        """
        st.markdown(canvas_html, unsafe_allow_html=True)
    elif (
        not st.session_state.require_manual_ticker
    ):  # Don't show initial message if asking for ticker
        st.markdown(
            """
            <div style="text-align: center; color: #a0aec0; width: 100%;">
                <h2 style="font-weight: 600;">Analysis Appears Here</h2>
                <p>Your generated financial analysis will be displayed in this canvas once you submit a query.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

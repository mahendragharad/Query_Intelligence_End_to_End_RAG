import streamlit as st
import requests
import os
from datetime import datetime

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
AUTH_HEADER_PREFIX = "Bearer "

st.set_page_config(
    page_title="RAG Intelligence Hub",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def get_auth_headers():
    token = st.session_state.get("auth_token")
    if token:
        return {"Authorization": f"{AUTH_HEADER_PREFIX}{token}"}
    return {}

def auth_request(endpoint: str, payload: dict, timeout: int = 60):
    return requests.post(
        f"{API_BASE_URL}{endpoint}",
        json=payload,
        timeout=timeout,
        headers=get_auth_headers(),
    )

# ─── SESSION STATE ──────────────────────────────────────────────────────────────
defaults = {
    "ingest_mode": "file",
    "last_results": None,
    "last_answer": None,
    "last_context": None,
    "last_query": None,
    "auth_token": None,
    "user_email": None,
    "auth_message": "",
    "auth_mode": "Login",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── API HEALTH CHECK ───────────────────────────────────────────────────────────
api_ok = False
try:
    health = requests.get(f"{API_BASE_URL}/health", timeout=5)
    api_ok = health.ok
except requests.exceptions.RequestException:
    pass

# ─── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap');

/* ── Reset & Base ─────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section.main {
    background: #06080F !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
.stDeployButton { display: none !important; }

/* ── SIDEBAR ──────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1120 0%, #0A0D18 100%) !important;
    border-right: 1px solid rgba(0, 212, 255, 0.12) !important;
    box-shadow: 4px 0 32px rgba(0, 0, 0, 0.5) !important;
    min-width: 310px !important;
    max-width: 310px !important;
    padding: 0 !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1.25rem 2rem 1.25rem !important;
    overflow-y: auto !important;
    height: 100vh !important;
}

[data-testid="stSidebarNav"] { display: none !important; }

/* ── MAIN CONTENT — gap from sidebar ── */
[data-testid="stAppViewContainer"] > section.main {
    margin-left: 0 !important;
    padding-left: 0 !important;
}

[data-testid="stMainBlockContainer"],
.main .block-container {
    padding: 2.5rem 3rem 3rem 3rem !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
}

/* ── SIDEBAR: Brand ── */
.sb-brand {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 0.25rem 0 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 1.5rem;
}
.sb-brand-icon {
    width: 42px; height: 42px; flex-shrink: 0;
    background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(124,58,237,0.2));
    border: 1px solid rgba(0,212,255,0.28);
    border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 0 20px rgba(0,212,255,0.12), inset 0 0 12px rgba(0,212,255,0.04);
}
.sb-brand-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.97rem; font-weight: 700;
    color: #F1F5F9; letter-spacing: -0.01em; line-height: 1.2;
}
.sb-brand-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem; color: #2D4A6A;
    letter-spacing: 0.14em; text-transform: uppercase;
    margin-top: 2px;
}

/* ── SIDEBAR: Section labels ── */
.sb-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem; font-weight: 600;
    color: #2D4A6A; letter-spacing: 0.2em;
    text-transform: uppercase;
    margin: 1.5rem 0 0.75rem;
    display: flex; align-items: center; gap: 8px;
}
.sb-label::after {
    content: '';
    flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.06), transparent);
}

/* ── SIDEBAR: Status badge ── */
.sb-status {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 12px; border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.67rem; font-weight: 500;
    margin-bottom: 1.25rem;
    width: 100%;
    letter-spacing: 0.04em;
}
.sb-status.ok  {
    background: rgba(0,212,255,0.06);
    border: 1px solid rgba(0,212,255,0.18);
    color: #00D4FF;
}
.sb-status.err {
    background: rgba(255,77,109,0.06);
    border: 1px solid rgba(255,77,109,0.18);
    color: #FF4D6D;
}
.sb-dot {
    width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}
.sb-dot.ok  { background: #00D4FF; box-shadow: 0 0 8px #00D4FF; animation: pulse-dot 2s infinite; }
.sb-dot.err { background: #FF4D6D; }

/* ── SIDEBAR: Mode pills ── */
.pill-row { display: flex; gap: 8px; margin-bottom: 1.1rem; }
.pill {
    flex: 1; padding: 7px 0; text-align: center;
    border-radius: 8px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.05em; text-transform: uppercase;
}
.pill.on  {
    background: rgba(0,212,255,0.10);
    border: 1px solid rgba(0,212,255,0.32);
    color: #00D4FF;
    box-shadow: 0 0 12px rgba(0,212,255,0.08);
}
.pill.off {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    color: #2D4A6A;
}

/* ── SIDEBAR: Logged-in badge ── */
.sb-logged-in {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 12px; border-radius: 8px;
    background: rgba(0,212,255,0.06);
    border: 1px solid rgba(0,212,255,0.18);
    color: #7DE8FF;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.67rem;
    margin-bottom: 0.75rem;
    word-break: break-all;
}

/* ── Streamlit global inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: rgba(5,8,16,0.9) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 9px !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    padding: 0.6rem 0.9rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(0,212,255,0.38) !important;
    box-shadow: 0 0 0 3px rgba(0,212,255,0.07) !important;
    outline: none !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label,
[data-testid="stFileUploader"] label {
    color: #3B5270 !important;
    font-size: 0.72rem !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: rgba(5,8,16,0.9) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 9px !important;
    color: #E2E8F0 !important;
    font-size: 0.85rem !important;
}
[data-testid="stSelectbox"] svg { fill: #3B5270 !important; }

/* ── Slider ── */
[data-testid="stSlider"] [data-testid="stTickBar"] { display: none !important; }
[data-testid="stSlider"] > div > div > div > div {
    background: linear-gradient(90deg, #00D4FF, #7C3AED) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, rgba(0,212,255,0.07), rgba(124,58,237,0.07)) !important;
    border: 1px solid rgba(0,212,255,0.28) !important;
    color: #00D4FF !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    border-radius: 9px !important;
    padding: 0.6rem 1.3rem !important;
    transition: all 0.22s cubic-bezier(0.4,0,0.2,1) !important;
    text-transform: uppercase !important;
    width: 100% !important;
}
.stButton > button:hover {
    border-color: rgba(0,212,255,0.6) !important;
    box-shadow: 0 0 22px rgba(0,212,255,0.16), 0 0 0 1px rgba(0,212,255,0.08) inset !important;
    transform: translateY(-1px) !important;
    color: #66E5FF !important;
    background: linear-gradient(135deg, rgba(0,212,255,0.13), rgba(124,58,237,0.11)) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(5,8,16,0.7) !important;
    border: 1px dashed rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(0,212,255,0.28) !important;
    box-shadow: 0 0 18px rgba(0,212,255,0.05) !important;
}
[data-testid="stFileUploaderDropzone"] { background: transparent !important; }
[data-testid="stFileUploaderDropzoneInstructions"] { color: #2D4A6A !important; }

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 9px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
    border: none !important;
}
div[class*="stSuccess"] {
    background: rgba(0,212,255,0.05) !important;
    border: 1px solid rgba(0,212,255,0.18) !important;
    border-left: 3px solid #00D4FF !important;
    border-radius: 9px !important;
    color: #7DE8FF !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.74rem !important;
}
div[class*="stError"] {
    background: rgba(255,77,109,0.05) !important;
    border: 1px solid rgba(255,77,109,0.18) !important;
    border-left: 3px solid #FF4D6D !important;
    border-radius: 9px !important;
    color: #FF8099 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.74rem !important;
}
div[class*="stInfo"] {
    background: rgba(124,58,237,0.05) !important;
    border: 1px solid rgba(124,58,237,0.18) !important;
    border-left: 3px solid #7C3AED !important;
    border-radius: 9px !important;
    color: #B09DFF !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.74rem !important;
}
div[class*="stWarning"] {
    background: rgba(245,158,11,0.05) !important;
    border: 1px solid rgba(245,158,11,0.18) !important;
    border-left: 3px solid #F59E0B !important;
    border-radius: 9px !important;
    color: #FCD34D !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.74rem !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #00D4FF !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: rgba(10,13,24,0.65) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 10px !important;
    margin-bottom: 0.6rem !important;
    overflow: hidden !important;
    transition: border-color 0.2s !important;
}
[data-testid="stExpander"]:hover { border-color: rgba(0,212,255,0.18) !important; }
[data-testid="stExpander"] summary {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.82rem !important; font-weight: 600 !important;
    color: #8BA3BE !important; padding: 0.8rem 1rem !important;
}
[data-testid="stExpander"] summary:hover { color: #C4D4E4 !important; }

/* ── JSON ── */
[data-testid="stJson"] {
    background: rgba(5,8,16,0.9) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 9px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.71rem !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
    gap: 0 !important;
    margin-bottom: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: #2D4A6A !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.78rem !important; font-weight: 600 !important;
    letter-spacing: 0.07em !important; text-transform: uppercase !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.75rem 1.4rem !important;
    transition: all 0.2s !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #00D4FF !important;
    border-bottom-color: #00D4FF !important;
    text-shadow: 0 0 14px rgba(0,212,255,0.35) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
[data-testid="stTabs"] [data-baseweb="tab-panel"] {
    padding: 2rem 0 0 !important;
    background: transparent !important;
}

/* ── Columns ── */
[data-testid="column"] { padding: 0 0.45rem !important; }
[data-testid="column"]:first-child { padding-left: 0 !important; }
[data-testid="column"]:last-child  { padding-right: 0 !important; }

/* ── Horizontal rule ── */
hr {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.05) !important;
    margin: 1.5rem 0 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #06080F; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.14); }

/* ─────────────────────────────────────────────────
   MAIN CONTENT COMPONENTS
───────────────────────────────────────────────── */

/* ── Page header ── */
.page-header {
    padding: 0.25rem 0 2.25rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 2.25rem;
    position: relative;
}
.header-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem; color: #00D4FF;
    letter-spacing: 0.2em; text-transform: uppercase;
    margin-bottom: 0.7rem;
    display: flex; align-items: center; gap: 10px;
}
.header-eyebrow::before {
    content: '';
    width: 22px; height: 1px;
    background: linear-gradient(90deg, transparent, #00D4FF);
}
.page-header h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.15rem; font-weight: 700;
    color: #F1F5F9; letter-spacing: -0.03em; line-height: 1.15;
    margin: 0 0 0.6rem;
}
.page-header h1 .accent { color: #00D4FF; }
.page-header h1 .dim    { color: #243348; }
.page-header p {
    font-size: 0.84rem; color: #3F5470;
    line-height: 1.65; max-width: 520px; margin: 0;
}

/* ── Query bar card ── */
.query-bar {
    background: rgba(10,13,24,0.8);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.5rem 1.6rem;
    margin-bottom: 1.75rem;
    position: relative; overflow: hidden;
    backdrop-filter: blur(14px);
    box-shadow: 0 4px 32px rgba(0,0,0,0.35);
}
.query-bar::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,212,255,0.38), transparent);
}
.qbar-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem; color: #00D4FF;
    letter-spacing: 0.16em; text-transform: uppercase;
    margin-bottom: 1rem;
    display: flex; align-items: center; gap: 8px;
}
.qbar-label::before {
    content: '';
    width: 3px; height: 10px;
    background: linear-gradient(180deg, #00D4FF, #7C3AED);
    border-radius: 2px;
    box-shadow: 0 0 6px rgba(0,212,255,0.6);
}

/* ── AI answer ── */
.ai-wrap {
    animation: fadeSlideIn 0.38s ease forwards;
    margin-top: 0.25rem;
}
.ai-header {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 0.9rem;
}
.ai-avatar {
    width: 34px; height: 34px; flex-shrink: 0;
    background: linear-gradient(135deg, #7C3AED, #00D4FF);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px;
    box-shadow: 0 0 18px rgba(124,58,237,0.35);
}
.ai-meta-label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.78rem; font-weight: 600; color: #4B6480;
}
.ai-meta-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem; color: #7C3AED; margin-left: 8px;
    letter-spacing: 0.1em;
}
.ai-bubble {
    background: linear-gradient(135deg, rgba(12,15,26,0.95), rgba(16,10,28,0.90));
    border: 1px solid rgba(124,58,237,0.2);
    border-radius: 4px 14px 14px 14px;
    padding: 1.5rem 1.75rem;
    position: relative;
    box-shadow: 0 8px 40px rgba(0,0,0,0.38);
    backdrop-filter: blur(16px);
}
.ai-bubble::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, rgba(124,58,237,0.5), rgba(0,212,255,0.35), transparent);
}
.ai-text {
    font-size: 0.895rem; color: #C4D4E4;
    line-height: 1.85; white-space: pre-wrap; margin: 0;
}
.ai-actions {
    display: flex; gap: 0.6rem; margin-top: 1rem; flex-wrap: wrap;
}
.ai-tag {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 11px; border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.63rem; letter-spacing: 0.07em;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    color: #3B5270;
}

/* ── Generate button ── */
.gen-hint {
    font-size: 0.76rem; color: #253645;
    font-family: 'Inter', sans-serif;
    line-height: 1.55; padding-top: 0.6rem;
}

/* ── Context header ── */
.ctx-header {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 1.25rem;
}
.ctx-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem; color: #3B5270;
    letter-spacing: 0.16em; text-transform: uppercase;
}
.ctx-badge {
    background: rgba(0,212,255,0.08);
    border: 1px solid rgba(0,212,255,0.2);
    color: #00D4FF;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem; padding: 3px 9px; border-radius: 4px;
}

/* ── Result card ── */
.result-card {
    background: rgba(10,13,24,0.75);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 11px;
    padding: 1.2rem 1.4rem;
    position: relative; overflow: hidden;
    backdrop-filter: blur(8px);
}
.result-card::before {
    content: '';
    position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    background: linear-gradient(180deg, #00D4FF, #7C3AED);
    border-radius: 0 2px 2px 0;
}
.result-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem; color: #00D4FF;
    letter-spacing: 0.14em; margin-bottom: 0.55rem;
    display: flex; align-items: center; gap: 5px;
}
.result-text {
    font-size: 0.845rem; color: #8BA3BE; line-height: 1.72; margin-bottom: 0.85rem;
}
.result-meta {
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 0.4rem;
    font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
    padding-top: 0.7rem;
    border-top: 1px solid rgba(255,255,255,0.05);
}
.result-src  { color: #2D4A6A; display: flex; align-items: center; gap: 5px; }
.result-score {
    background: rgba(0,212,255,0.08);
    border: 1px solid rgba(0,212,255,0.2);
    color: #00D4FF; padding: 2px 9px; border-radius: 5px;
    font-size: 0.62rem;
}

/* ── Empty state ── */
.empty-state {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 3.5rem 2rem; text-align: center;
    background: rgba(10,13,24,0.4);
    border: 1px dashed rgba(255,255,255,0.07);
    border-radius: 14px;
    margin-top: 0.5rem;
}
.empty-icon  { font-size: 2rem; margin-bottom: 1rem; opacity: 0.5; }
.empty-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.9rem; font-weight: 600; color: #243348; margin-bottom: 0.4rem;
}
.empty-sub { font-size: 0.77rem; color: #1A2C3D; line-height: 1.55; }

/* ── Footer ── */
.dash-footer {
    margin-top: 3.5rem; padding-top: 1.25rem;
    border-top: 1px solid rgba(255,255,255,0.05);
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 0.5rem;
}
.dash-footer span {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem; color: #192535; letter-spacing: 0.08em;
}

/* ── Animations ── */
@keyframes pulse-dot {
    0%, 100% { opacity: 1;   box-shadow: 0 0 8px #00D4FF; }
    50%       { opacity: 0.4; box-shadow: 0 0 3px #00D4FF; }
}
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes glow-pulse {
    0%, 100% { box-shadow: 0 0 24px rgba(0,0,0,0.4), 0 0 0 1px rgba(124,58,237,0.08) inset; }
    50%       { box-shadow: 0 0 40px rgba(0,0,0,0.45), 0 0 30px rgba(124,58,237,0.1), 0 0 0 1px rgba(0,212,255,0.06) inset; }
}
.fade-in  { animation: fadeSlideIn 0.38s ease forwards; }
.glow-ani { animation: glow-pulse 4s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-brand-icon">⚡</div>
        <div>
            <div class="sb-brand-name">RAG Intelligence</div>
            <div class="sb-brand-tag">Knowledge Hub v2</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # API status
    host_label = API_BASE_URL.replace("http://", "").replace("https://", "")
    if api_ok:
        st.markdown(f"""
        <div class="sb-status ok">
            <div class="sb-dot ok"></div>
            API LIVE &nbsp;·&nbsp; {host_label}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sb-status err">
            <div class="sb-dot err"></div>
            API OFFLINE — start FastAPI first
        </div>
        """, unsafe_allow_html=True)

    # ── Auth panel ──────────────────────────────────────
    st.markdown('<div class="sb-label">Account</div>', unsafe_allow_html=True)

    if st.session_state.auth_token:
        st.markdown(
            f'<div class="sb-logged-in">✓ &nbsp;{st.session_state.user_email}</div>',
            unsafe_allow_html=True
        )
        if st.button("Sign out", key="logout_btn", use_container_width=True):
            st.session_state.auth_token  = None
            st.session_state.user_email  = None
            st.session_state.auth_message = "Signed out."
            st.rerun()
    else:
        auth_mode = st.radio(
            "auth_action", ["Login", "Register"],
            index=0, horizontal=True,
            key="auth_mode", label_visibility="collapsed"
        )
        st.text_input("Email", key="auth_email", label_visibility="visible")
        st.text_input("Password", type="password", key="auth_password", label_visibility="visible")

        if auth_mode == "Register":
            if st.button("Create account", key="register_btn", use_container_width=True):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/register",
                        json={"email": st.session_state.auth_email,
                              "password": st.session_state.auth_password},
                        timeout=30,
                    )
                    st.session_state.auth_message = (
                        "Account created. Please sign in."
                        if resp.ok else
                        resp.json().get("detail", resp.text)
                    )
                except Exception as e:
                    st.session_state.auth_message = str(e)
        else:
            if st.button("Sign in", key="login_btn", use_container_width=True):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/login",
                        json={"email": st.session_state.auth_email,
                              "password": st.session_state.auth_password},
                        timeout=30,
                    )
                    if resp.ok:
                        data = resp.json()
                        st.session_state.auth_token  = data.get("access_token")
                        st.session_state.user_email  = st.session_state.auth_email
                        st.session_state.auth_message = ""
                        st.rerun()
                    else:
                        st.session_state.auth_message = resp.json().get("detail", resp.text)
                except Exception as e:
                    st.session_state.auth_message = str(e)

    if st.session_state.auth_message:
        st.info(st.session_state.auth_message)

    # ── Ingest source toggle ────────────────────────────
    st.markdown('<div class="sb-label">Ingest Source</div>', unsafe_allow_html=True)

    file_cls = "on" if st.session_state.ingest_mode == "file" else "off"
    url_cls  = "on" if st.session_state.ingest_mode == "url"  else "off"
    st.markdown(f"""
    <div class="pill-row">
        <div class="pill {file_cls}">📄 File</div>
        <div class="pill {url_cls}">🌐 URL</div>
    </div>
    """, unsafe_allow_html=True)

    col_f, col_u = st.columns(2)
    with col_f:
        if st.button("File", key="mode_file", use_container_width=True):
            st.session_state.ingest_mode = "file"
            st.rerun()
    with col_u:
        if st.button("URL", key="mode_url", use_container_width=True):
            st.session_state.ingest_mode = "url"
            st.rerun()

    # ── FILE mode ───────────────────────────────────────
    if st.session_state.ingest_mode == "file":
        st.markdown('<div class="sb-label">Upload Document</div>', unsafe_allow_html=True)
        pdf_file = st.file_uploader("PDF file", type=["pdf"], label_visibility="collapsed")
        st.caption("Accepts PDF up to 50 MB")
        pdf_collection = st.text_input("Collection name", value="documents", key="pdf_collection")

        if st.button("⬆  Ingest Document", key="pdf_upload", use_container_width=True):
            if pdf_file is not None:
                with st.spinner("Embedding document…"):
                    try:
                        files = {"file": (pdf_file.name, pdf_file.getvalue(), pdf_file.type)}
                        resp = requests.post(
                            f"{API_BASE_URL}/upload",
                            files=files,
                            params={"collection_name": pdf_collection},
                            timeout=300,
                            headers=get_auth_headers(),
                        )
                        if resp.ok:
                            st.success(f"✓ Ingested: {pdf_file.name}")
                            st.json(resp.json())
                        else:
                            st.error(f"Upload failed: {resp.text}")
                    except requests.exceptions.Timeout:
                        st.error("Timed out — PDF may be too large.")
                    except Exception as e:
                        st.error(str(e))
            else:
                st.warning("Select a PDF first.")

    # ── URL mode ────────────────────────────────────────
    else:
        st.markdown('<div class="sb-label">Web Source</div>', unsafe_allow_html=True)
        web_url        = st.text_input("Webpage URL", placeholder="https://example.com/article", key="web_url")
        web_collection = st.text_input("Collection name", value="documents", key="web_coll")
        web_strategy   = st.selectbox("Chunking strategy", ["semantic", "headers"], key="web_strat")

        if st.button("⬆  Ingest URL", key="url_ingest", use_container_width=True):
            if web_url:
                with st.spinner("Fetching & chunking page…"):
                    try:
                        payload = {"url": web_url, "strategy": web_strategy, "collection_name": web_collection}
                        resp = requests.post(
                            f"{API_BASE_URL}/ingest/url", json=payload,
                            timeout=300, headers=get_auth_headers()
                        )
                        if resp.ok:
                            st.success("✓ URL ingested successfully")
                            st.json(resp.json())
                        else:
                            st.error(f"Ingestion failed: {resp.text}")
                    except requests.exceptions.Timeout:
                        st.error("Request timed out.")
                    except Exception as e:
                        st.error(str(e))
            else:
                st.warning("Enter a URL first.")

        st.markdown('<div class="sb-label">Chunk Preview</div>', unsafe_allow_html=True)
        preview_url      = st.text_input("URL to preview", placeholder="https://example.com", key="preview_url")
        preview_strategy = st.selectbox("Strategy", ["semantic", "headers"], key="prev_strat")

        if st.button("👁  Preview Chunks", key="preview_btn", use_container_width=True):
            if preview_url:
                with st.spinner("Generating preview…"):
                    try:
                        payload = {"url": preview_url, "strategy": preview_strategy, "collection_name": "documents"}
                        resp = requests.post(
                            f"{API_BASE_URL}/chunk/url", json=payload,
                            timeout=60, headers=get_auth_headers()
                        )
                        if resp.ok:
                            result    = resp.json()
                            chunk_cnt = result.get("chunk_count", 0)
                            st.success(f"✓ {chunk_cnt} chunks generated")
                            for i, chunk in enumerate(result.get("preview", []), 1):
                                with st.expander(f"Chunk {i}", expanded=(i == 1)):
                                    st.caption(chunk.get("text", "")[:300] + "…")
                                    st.json(chunk.get("metadata", {}))
                        else:
                            st.error(f"Preview failed: {resp.text}")
                    except requests.exceptions.Timeout:
                        st.error("Request timed out.")
                    except Exception as e:
                        st.error(str(e))
            else:
                st.warning("Enter a URL to preview.")


# ─── MAIN AREA ─────────────────────────────────────────────────────────────────
if not st.session_state.auth_token:
    st.markdown("""
    <div class="empty-state fade-in" style="margin-top:3rem;">
        <div class="empty-icon">🔐</div>
        <div class="empty-title">Authentication required</div>
        <div class="empty-sub">Sign in or create an account in the sidebar<br>to access the intelligence hub.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Page header ────────────────────────────────────────
st.markdown("""
<div class="page-header fade-in">
    <div class="header-eyebrow">Retrieval-Augmented Generation</div>
    <h1>Query <span class="accent">Intelligence</span> <span class="dim">Hub</span></h1>
    <p>Search your ingested knowledge base or generate grounded AI answers directly from your documents.</p>
</div>
""", unsafe_allow_html=True)

# ── Query configuration bar ─────────────────────────────
st.markdown("""
<div class="query-bar fade-in">
    <div class="qbar-label">Query Configuration</div>
</div>
""", unsafe_allow_html=True)

col_q, col_coll, col_k = st.columns([3, 1.4, 1])
with col_q:
    query = st.text_input(
        "Search query",
        placeholder="What does this document say about…",
        key="main_query",
        label_visibility="collapsed",
    )
with col_coll:
    query_collection = st.text_input("Collection", value="documents", key="q_coll")
with col_k:
    top_k = st.slider("Top K", min_value=1, max_value=10, value=5)

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────
tab_answer, tab_search = st.tabs(["✦  AI Answer", "🔍  Context Retrieval"])

# ─────────────────────────────────────────────────
# TAB 1 — AI Answer Generation
# ─────────────────────────────────────────────────
with tab_answer:
    col_btn, col_hint = st.columns([1, 3])
    with col_btn:
        answer_btn = st.button("✦  Generate Answer", key="answer_btn")
    with col_hint:
        st.markdown(
            '<p class="gen-hint">Retrieves top context chunks, then produces a grounded answer.'
            ' (Ollama preferred · NVIDIA fallback)</p>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    if answer_btn and query:
        with st.spinner("Retrieving context and generating answer…"):
            try:
                payload = {"query": query, "collection_name": query_collection, "top_k": top_k}
                resp = requests.post(
                    f"{API_BASE_URL}/answer", json=payload,
                    timeout=180, headers=get_auth_headers()
                )
                if resp.ok:
                    result      = resp.json()
                    answer_text = result.get("answer", "")
                    st.session_state.last_answer  = answer_text
                    st.session_state.last_context = result.get("context", [])
                    st.session_state.last_query   = query

                    if answer_text:
                        ts = datetime.now().strftime("%H:%M")
                        st.markdown(f"""
                        <div class="ai-wrap">
                            <div class="ai-header">
                                <div class="ai-avatar">✦</div>
                                <div>
                                    <span class="ai-meta-label">AI Answer</span>
                                    <span class="ai-meta-time">generated {ts}</span>
                                </div>
                            </div>
                            <div class="ai-bubble glow-ani">
                                <p class="ai-text">{answer_text}</p>
                            </div>
                            <div class="ai-actions">
                                <span class="ai-tag">📋 Copy via browser</span>
                                <span class="ai-tag">📚 {top_k} chunks used</span>
                                <span class="ai-tag">🗂 {query_collection}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("Answer generation produced no output. Check the Context Retrieval tab.")
                else:
                    st.error(f"AI answer failed: {resp.text}")
            except requests.exceptions.Timeout:
                st.error("⏱ Request timed out. Try reducing Top K or checking server logs.")
            except Exception as e:
                st.error(str(e))

    elif answer_btn:
        st.warning("Enter a query first.")

    elif (
        st.session_state.last_answer
        and st.session_state.last_query == query
        and not answer_btn
    ):
        cached_text = st.session_state.last_answer
        cached_ctx  = st.session_state.last_context or []
        st.markdown(f"""
        <div class="ai-wrap">
            <div class="ai-header">
                <div class="ai-avatar">✦</div>
                <div>
                    <span class="ai-meta-label">AI Answer</span>
                    <span class="ai-meta-time">cached result</span>
                </div>
            </div>
            <div class="ai-bubble">
                <p class="ai-text">{cached_text}</p>
            </div>
            <div class="ai-actions">
                <span class="ai-tag">📋 Copy via browser</span>
                <span class="ai-tag">📚 {len(cached_ctx)} chunks</span>
                <span class="ai-tag">🗂 {query_collection}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="empty-state fade-in">
            <div class="empty-icon">✦</div>
            <div class="empty-title">No answer yet</div>
            <div class="empty-sub">Enter a query above and click Generate Answer<br>to get a grounded AI response from your documents.</div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# TAB 2 — Context Retrieval
# ─────────────────────────────────────────────────
with tab_search:
    search_btn = st.button("🔍  Run Retrieval", key="search_btn")
    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    if search_btn and query:
        with st.spinner("Searching vector store…"):
            try:
                payload = {"query": query, "collection_name": query_collection, "top_k": top_k}
                resp = requests.post(
                    f"{API_BASE_URL}/query", json=payload,
                    timeout=60, headers=get_auth_headers()
                )
                if resp.ok:
                    result = resp.json()
                    chunks = result.get("results", [])
                    st.session_state.last_results = chunks
                    count  = result.get("result_count", len(chunks))
                    st.success(f"✓ Retrieved {count} chunk{'s' if count != 1 else ''}")
                else:
                    st.error(f"Query failed: {resp.text}")
            except requests.exceptions.Timeout:
                st.error("Query timed out.")
            except Exception as e:
                st.error(str(e))

    elif search_btn:
        st.warning("Enter a query to search.")

    # Resolve which chunks to display
    chunks_to_show = st.session_state.last_results or []
    if not chunks_to_show and st.session_state.last_context:
        chunks_to_show = st.session_state.last_context
        st.info("Showing context from the last AI Answer. Run retrieval for a fresh search.")

    if chunks_to_show:
        chunk_count = len(chunks_to_show)
        st.markdown(f"""
        <div class="ctx-header fade-in">
            <span class="ctx-label">Retrieved Chunks</span>
            <span class="ctx-badge">{chunk_count}</span>
        </div>
        """, unsafe_allow_html=True)

        for i, item in enumerate(chunks_to_show, 1):
            text    = item.get("text", "N/A")
            meta    = item.get("metadata", {})
            source  = meta.get("source", "Unknown")
            score   = item.get("rerank_score")
            display = text[:600] + ("…" if len(text) > 600 else "")

            score_html = (
                f'<span class="result-score">score: {score:.4f}</span>'
                if score is not None else ""
            )

            with st.expander(f"Chunk {i:02d}  —  {source}", expanded=(i == 1)):
                st.markdown(f"""
                <div class="result-card">
                    <div class="result-num">CHUNK · {i:02d}</div>
                    <div class="result-text">{display}</div>
                    <div class="result-meta">
                        <span class="result-src">📁 {source}</span>
                        {score_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if meta:
                    st.caption("Metadata")
                    st.json(meta)
    else:
        st.markdown("""
        <div class="empty-state fade-in">
            <div class="empty-icon">🔍</div>
            <div class="empty-title">No chunks retrieved yet</div>
            <div class="empty-sub">Enter a query above and click Run Retrieval<br>to see the top matching chunks from your knowledge base.</div>
        </div>
        """, unsafe_allow_html=True)


# ── Footer ─────────────────────────────────────────────
st.markdown(f"""
<div class="dash-footer">
    <span>RAG INTELLIGENCE HUB · BUILD 2.0</span>
    <span>{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}  UTC+5:30</span>
    <span>API → {API_BASE_URL}</span>
</div>
""", unsafe_allow_html=True)
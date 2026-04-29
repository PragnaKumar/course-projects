"""
app.py — Entry point for Moodreads.

Handles:
- Ollama auto-start
- Resource caching (router, memory, prefs)
- Session state init
- Page routing → ui/ modules
"""

import time
import subprocess
import requests
import streamlit as st

from graph.router import build_router
from memory.conversation import get_memory, generate_user_id
from memory.preference import PreferenceStore
from ui.styles import inject_css, TAB_CONFIG
from ui.landing_page import render_landing
from ui.leisure import render_leisure
from ui.research import render_research
from ui.tb import render_textbook


# ─── Ollama auto-start ───────────────────────────────────────────────────────
def is_ollama_running(base_url="http://localhost:11434") -> bool:
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=3)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def start_ollama() -> bool:
    if is_ollama_running():
        return True
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(10):
            time.sleep(1)
            if is_ollama_running():
                return True
        return False
    except FileNotFoundError:
        return False


@st.cache_resource
def ensure_ollama() -> bool:
    return start_ollama()


# ─── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Moodreads · AI Book Recommender",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()


# ─── Ollama check ─────────────────────────────────────────────────────────────
if not ensure_ollama():
    st.error(
        "⚠️ Ollama could not start automatically. "
        "Please run `ollama serve` in a terminal, then refresh.",
        icon="🦙"
    )
    st.stop()


# ─── Cached resources ────────────────────────────────────────────────────────
@st.cache_resource
def load_app():
    memory = get_memory()
    return build_router(memory=memory)

@st.cache_resource
def load_prefs():
    return PreferenceStore()

app   = load_app()
prefs = load_prefs()


# ─── Session state init ───────────────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.session_state.user_id = generate_user_id()

if "page" not in st.session_state:
    st.session_state.page = "landing"

for key in [cfg["msg_key"] for cfg in TAB_CONFIG.values()]:
    if key not in st.session_state:
        st.session_state[key] = []

user_id = st.session_state.user_id


# ─── Page routing ─────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "landing":
    render_landing()
elif page == "leisure":
    render_leisure(app, prefs, user_id)
elif page == "research":
    render_research(app, prefs, user_id)
elif page == "textbook":
    render_textbook(app, prefs, user_id)
else:
    st.session_state.page = "landing"
    st.rerun()
"""
ui/styles.py

Shared CSS, constants, and helpers used across all UI pages.
Import and call inject_css() at the top of app.py once.
"""

import streamlit as st

# ─── Shared constants ─────────────────────────────────────────────────────────

ROUTE_EMOJI = {
    "leisure_books":   "📖 Fiction",
    "research_papers": "📄 Research",
    "textbooks":       "📘 Textbook",
}

MOOD_KEYWORDS = [
    "sad", "happy", "anxious", "stressed", "lonely", "bored", "tired",
    "excited", "curious", "focused", "motivated", "nostalgic", "romantic",
    "scared", "angry", "hopeful", "overwhelmed", "adventurous",
]

TAB_CONFIG = {
    "leisure": {
        "icon":        "📖",
        "title":       "Fiction & Leisure",
        "description": "Mood-based fiction, novels, audiobooks and ebooks",
        "msg_key":     "leisure_messages",
        "placeholder": "I'm feeling lonely and want something heartwarming...",
        "hints": [
            "I'm feeling sad, something uplifting please",
            "Fast-paced thriller for the weekend",
            "Cozy read for a stressed evening",
            "Romcom — I'm in a happy mood",
        ],
    },
    "research": {
        "icon":        "📄",
        "title":       "Research Papers",
        "description": "Academic papers, ArXiv articles and scientific journals",
        "msg_key":     "research_messages",
        "placeholder": "Find me recent papers on graph neural networks...",
        "hints": [
            "Latest papers on large language models",
            "Climate change economics research 2024",
            "Survey on reinforcement learning",
            "Attention mechanisms in transformers",
        ],
    },
    "textbook": {
        "icon":        "📘",
        "title":       "Textbooks",
        "description": "Course materials, textbooks and academic learning resources",
        "msg_key":     "tb_messages",
        "placeholder": "I need a beginner-friendly machine learning textbook...",
        "hints": [
            "Beginner textbook for linear algebra",
            "Graduate level deep learning book",
            "Introduction to algorithms for undergrads",
            "Best book to learn Python from scratch",
        ],
    },
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def detect_mood(text: str) -> str:
    """Lightweight keyword mood detection for badge display."""
    lower = text.lower()
    for mood in MOOD_KEYWORDS:
        if mood in lower:
            return mood
    return ""


def render_badges(msg: dict):
    """Render mood + route badges for an assistant message."""
    badges = ""
    if msg.get("mood"):
        badges += f'<span class="mood-badge">🎭 {msg["mood"]}</span>'
    if msg.get("route"):
        badges += f'<span class="route-badge">{ROUTE_EMOJI.get(msg["route"], msg["route"])}</span>'
    if badges:
        st.markdown(badges, unsafe_allow_html=True)


# ─── CSS ──────────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0f0e0c;
    color: #f0ece4;
}
h1, h2, h3 { font-family: 'Playfair Display', serif; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #141210 !important;
    border-right: 1px solid #2a2620;
    min-width: 230px !important;
    max-width: 230px !important;
}

/* ── Landing ── */
.landing-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    text-align: center;
    padding: 1rem 1rem;
}
.landing-logo {
    font-size: 4rem;
    margin-bottom: 0.5rem;
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50%       { transform: translateY(-10px); }
}
.landing-title {
    font-family: 'Playfair Display', serif;
    font-size: 4rem;
    font-weight: 700;
    color: #f0ece4;
    line-height: 1.1;
    margin-bottom: 0.3rem;
}
.landing-title span { color: #c8a97e; font-style: italic; }
.landing-sub {
    color: #a09880;
    font-size: 1.15rem;
    max-width: 520px;
    margin: 0 auto 2rem auto;
    line-height: 1.5;
}
.card {
    background: #1a1814;
    border: 1px solid #2e2b26;
    border-radius: 16px;
    padding: 28px 24px;
    transition: all 0.2s ease;
    text-align: left;
    height: 100%;
}
.card:hover {
    border-color: #c8a97e55;
    background: #211f1a;
    transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.card-icon  { font-size: 2rem; margin-bottom: 12px; }
.card-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.15rem;
    color: #f0ece4;
    margin-bottom: 8px;
}
.card-desc  { color: #a09880; font-size: 0.85rem; line-height: 1.5; }
.card-tag {
    display: inline-block;
    margin-top: 14px;
    background: #2a2420;
    border: 1px solid #c8a97e33;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.75rem;
    color: #c8a97e;
}
.landing-footer { color: #4a4640; font-size: 0.8rem; margin-top: 1rem; }

/* ── Chat pages ── */
.page-header {
    padding: 1.8rem 0 1rem 0;
    border-bottom: 1px solid #2a2620;
    margin-bottom: 1.4rem;
    display: flex;
    align-items: center;
    gap: 14px;
}
.page-header .page-icon { font-size: 2rem; }
.page-header h2 {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    color: #f0ece4;
    margin: 0;
}
.page-header .page-desc { color: #a09880; font-size: 0.88rem; margin-top: 2px; }
.hints-box {
    background: #1a1814;
    border: 1px solid #2e2b26;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 1.2rem;
    font-size: 0.85rem;
    color: #a09880;
    line-height: 1.8;
}

/* ── Badges ── */
.mood-badge {
    display: inline-block;
    background: #2a2420;
    border: 1px solid #c8a97e55;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: #c8a97e;
    margin-bottom: 8px;
    margin-right: 4px;
}
.route-badge {
    display: inline-block;
    background: #1e2a1e;
    border: 1px solid #4a7c4a55;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: #7abf7a;
    margin-bottom: 8px;
}

/* ── Chat ── */
[data-testid="stChatMessage"] {
    background-color: #1a1814;
    border: 1px solid #2e2b26;
    border-radius: 12px;
    margin-bottom: 8px;
    padding: 12px;
}
[data-testid="stChatInput"] textarea {
    background-color: #1a1814 !important;
    border: 1px solid #3a3630 !important;
    border-radius: 10px !important;
    color: #f0ece4 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #1e1c18;
    border: 1px solid #3a3630;
    color: #a09880;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    padding: 6px 14px;
    width: 100%;
}
.stButton > button:hover {
    background: #2a2620;
    border-color: #c8a97e55;
    color: #f0ece4;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0f0e0c; }
::-webkit-scrollbar-thumb { background: #3a3630; border-radius: 3px; }
                
/* ── Remove Streamlit default top padding ── */
.block-container {
    padding-top: 1rem !important;    /* was ~4rem by default */
    padding-bottom: 1rem !important;
}

/* Hide the Streamlit top header bar entirely */
[data-testid="stHeader"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)
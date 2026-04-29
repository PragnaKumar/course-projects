"""
ui/chat_base.py

Shared sidebar and chat logic used by all three chat pages.
Each page calls render_chat_page(page_key, app, prefs, user_id).
"""

import traceback
import streamlit as st
from memory.conversation import get_thread_config, clear_conversation
from ui.styles import TAB_CONFIG, ROUTE_EMOJI, detect_mood, render_badges


def render_sidebar(page_key: str, user_id: str, prefs):
    """Render the sidebar for a chat page."""
    cfg = TAB_CONFIG[page_key]

    with st.sidebar:
        # Back to landing
        if st.button("← Back to Moodreads", key="back_btn", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()

        st.divider()

        # Current section label
        st.markdown(
            f"<div style='font-family:Playfair Display,serif; font-size:1.1rem; "
            f"color:#f0ece4;'>{cfg['icon']} {cfg['title']}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='color:#a09880; font-size:0.8rem; margin-bottom:1rem;'>"
            f"{cfg['description']}</div>",
            unsafe_allow_html=True
        )

        st.divider()

        # Switch to other sections
        st.markdown(
            "<div style='font-size:0.78rem; color:#706860; margin-bottom:8px;'>"
            "SWITCH TO</div>",
            unsafe_allow_html=True
        )
        for other_key, other_cfg in TAB_CONFIG.items():
            if other_key != page_key:
                if st.button(
                    f"{other_cfg['icon']} {other_cfg['title']}",
                    key=f"switch_{other_key}",
                    use_container_width=True
                ):
                    st.session_state.page = other_key
                    st.rerun()

        st.divider()

        # Clear history — only for this tab
        if st.button(
            f"🗑 Clear {cfg['title']} history",
            key=f"clear_{page_key}",
            use_container_width=True
        ):
            st.session_state[cfg["msg_key"]] = []
            clear_conversation(user_id)
            st.rerun()

        st.divider()

        # User's top moods
        top_moods = prefs.get_top_moods(user_id, top_n=3)
        if top_moods:
            st.markdown(
                "<div style='font-size:0.8rem; color:#a09880; margin-bottom:6px;'>"
                "Your usual moods</div>",
                unsafe_allow_html=True
            )
            st.markdown(" · ".join(f"`{m}`" for m in top_moods))
            st.divider()

        st.caption(f"Session `{user_id[:8]}...`")
        st.caption("LangGraph · Ollama · qwen2.5:7b")


def render_chat_page(page_key: str, app, prefs, user_id: str):
    """
    Render a full chat page for the given section key.

    Args:
        page_key: One of 'leisure', 'research', 'textbook'
        app:      Compiled LangGraph router
        prefs:    PreferenceStore instance
        user_id:  Current session user ID
    """
    cfg     = TAB_CONFIG[page_key]
    msg_key = cfg["msg_key"]

    # Sidebar
    render_sidebar(page_key, user_id, prefs)

    # ── Back button on main page ──────────────────────────────────────────────
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"]:has(div.back-button-col) {
        margin-bottom: 0 !important;
    }
    .back-button-col .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #706860 !important;
        font-size: 0.85rem !important;
        padding: 0 4px !important;
        width: auto !important;
        text-align: left !important;
        box-shadow: none !important;
    }
    .back-button-col .stButton > button:hover {
        color: #c8a97e !important;
        background: transparent !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    back_col, _ = st.columns([1, 9])
    with back_col:
        st.markdown('<div class="back-button-col">', unsafe_allow_html=True)
        if st.button("← Back", key="back_main"):
            st.session_state.page = "landing"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='page-header'>
        <div class='page-icon'>{cfg['icon']}</div>
        <div>
            <h2>{cfg['title']}</h2>
            <div class='page-desc'>{cfg['description']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hints bar
    st.markdown(
        "<div class='hints-box'>💡 " +
        " &nbsp;·&nbsp; ".join(f"<em>{h}</em>" for h in cfg["hints"]) +
        "</div>",
        unsafe_allow_html=True
    )

    # Chat history
    for msg in st.session_state[msg_key]:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                render_badges(msg)
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input(cfg["placeholder"], key=f"input_{msg_key}"):
        st.session_state[msg_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        thread_config = get_thread_config(user_id)

        with st.spinner("Finding recommendations..."):
            try:
                result   = app.invoke(
                    {"user_input": prompt, "route": "", "response": ""},
                    config=thread_config,
                )
                response = result.get("response", "Sorry, I couldn't generate a recommendation.")
                route    = result.get("route", "")
                mood     = detect_mood(prompt)

                prefs.save(
                    user_id=user_id,
                    mood=mood,
                    content_type=route,
                    query=prompt,
                    route=route,
                )

            except Exception as e:
                tb       = traceback.format_exc()
                print(tb)   # full traceback in terminal
                response = f"⚠️ Something went wrong: `{str(e)}`\n\n```\n{tb}\n```"
                route    = ""
                mood     = ""

        st.session_state[msg_key].append({
            "role":    "assistant",
            "content": response,
            "route":   route,
            "mood":    mood,
        })

        with st.chat_message("assistant"):
            render_badges({"mood": mood, "route": route})
            st.markdown(response)
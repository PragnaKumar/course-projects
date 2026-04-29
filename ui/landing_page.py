"""
ui/landing.py

Moodreads landing page — hero section + three section cards.
"""

import streamlit as st


def render_landing():
    st.markdown("""
    <div class='landing-wrap'>
        <div class='landing-logo'>📚</div>
        <div class='landing-title'>Mood<span>reads</span></div>
        <div class='landing-sub'>
            Your mood-aware reading companion.<br>
            For books are like portable magic!
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Three section cards
    col1, col2, col3 = st.columns(3, gap="medium")

    cards = [
        (
            "leisure", "📖", "Fiction & Leisure",
            "Novels, audiobooks and ebooks picked for your mood.",
            "mood-based"
        ),
        (
            "research", "📄", "Research Papers",
            "Academic papers and ArXiv articles on any topic.",
            "arxiv · journals"
        ),
        (
            "textbook", "📘", "Textbooks",
            "Course materials and textbooks for any subject or level.",
            "undergraduate · graduate · high school · preschool "
        ),
    ]

    for col, (key, icon, title, desc, tag) in zip([col1, col2, col3], cards):
        with col:
            st.markdown(f"""
            <div class='card'>
                <div class='card-icon'>{icon}</div>
                <div class='card-title'>{title}</div>
                <div class='card-desc'>{desc}</div>
                <div class='card-tag'>{tag}</div>
            </div>
            """, unsafe_allow_html=True)
            # Spacer so button sits just below the card
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button(f"Open {title} →", key=f"land_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

    st.markdown(
        "<div class='landing-footer' style='text-align:center; margin-top:2rem;'>"
        "Powered by LangGraph · Ollama · qwen2.5:7b"
        "</div>",
        unsafe_allow_html=True
    )
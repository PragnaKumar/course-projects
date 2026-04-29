"""ui/research_page.py"""
from ui.chat_base import render_chat_page

def render_research(app, prefs, user_id: str):
    render_chat_page("research", app, prefs, user_id)
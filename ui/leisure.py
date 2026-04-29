"""ui/leisure_page.py"""
from ui.chat_base import render_chat_page

def render_leisure(app, prefs, user_id: str):
    render_chat_page("leisure", app, prefs, user_id)
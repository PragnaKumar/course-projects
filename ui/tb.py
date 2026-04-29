"""ui/textbook_page.py"""
from ui.chat_base import render_chat_page

def render_textbook(app, prefs, user_id: str):
    render_chat_page("textbook", app, prefs, user_id)
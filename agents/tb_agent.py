import json
import re
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from models.llm import get_llm
from tools.google_books import google_books_search
from logic.mood_wrapper import map_mood_to_query

llm = get_llm(temperature=0.3)


class TextbookState(TypedDict, total=False):
    user_input: str
    subject: str
    level: str
    author: str
    search_query: str
    tool_results: list
    response: str


def _parse_json_from_llm(text: str) -> dict:
    try:
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return {}


def analyze_textbook_intent(state: TextbookState):
    user_input = state.get("user_input", "")
    prompt = f"""
You are an educational intent extraction assistant.
From the user message below, extract:
- subject: the academic subject or course topic (e.g. "linear algebra", "organic chemistry", "machine learning")
- level: the academic level if mentioned — one of: beginner, high school, undergraduate, graduate, professional. Default to "undergraduate" if unclear.
- author: preferred author or publisher if mentioned. Empty string if none.

Respond ONLY with valid JSON. No explanation. No markdown.
Example: {{"subject": "machine learning", "level": "undergraduate", "author": "Bishop"}}

User message: {user_input}
"""
    raw    = llm.invoke([HumanMessage(content=prompt)]).content
    parsed = _parse_json_from_llm(raw)
    return {
        "subject": parsed.get("subject", user_input),
        "level":   parsed.get("level", "undergraduate"),
        "author":  parsed.get("author", ""),
    }


def build_search_query(state: TextbookState):
    subject = state.get("subject", state.get("user_input", ""))
    level   = state.get("level", "")
    author  = state.get("author", "")

    parts = [subject, "textbook"]
    if level and level not in ("undergraduate", ""):
        parts.append(level)
    if author:
        parts.append(f"author:{author}")

    return {"search_query": " ".join(parts)}


def tool_node(state: TextbookState):
    results = google_books_search.invoke({
        "query":       state.get("search_query", "textbook"),
        "max_results": 8
    })
    return {"tool_results": results}


def generate_response(state: TextbookState):
    system = SystemMessage(content=(
        "You are an academic course advisor specializing in textbook recommendations. "
        "Recommend ONLY textbooks from the provided candidates. Never recommend fiction. Never invent titles."
    ))
    prompt = f"""
User request: {state.get("user_input", "")}
Subject area: {state.get("subject", "")}
Academic level: {state.get("level", "undergraduate")}
Preferred author: {state.get("author", "not specified")}

Textbook candidates from Google Books:
{state.get("tool_results", [])}

Task:
- Select the 3 most appropriate textbooks from the candidates above ONLY. Never invent titles.
- For each textbook provide:
  * **Title** — Author(s) — Publisher if available
  * 2-3 sentences explaining WHY this textbook suits the user's level and subject
  * Ebook: Yes/No based on isEbook field
  * 🔗 Link: use the best_link field from the candidate data. Always include it.
- Use a clear, helpful, and structured tone.
- NEVER recommend a textbook without a link.
"""
    resp = llm.invoke([system, HumanMessage(content=prompt)]).content
    return {"response": resp}


def build_tb_agent():
    g = StateGraph(TextbookState)
    g.add_node("analyze", analyze_textbook_intent)
    g.add_node("plan",    build_search_query)
    g.add_node("search",  tool_node)
    g.add_node("respond", generate_response)

    g.set_entry_point("analyze")
    g.add_edge("analyze", "plan")
    g.add_edge("plan",    "search")
    g.add_edge("search",  "respond")
    g.add_edge("respond", END)
    return g.compile()
import json
import re
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from models.llm import get_llm
from tools.google_books import google_books_search
from logic.mood_wrapper import map_mood_to_query

llm = get_llm(temperature=0.4)


class LeisureState(TypedDict, total=False):
    user_input: str
    mood: str
    genre: str
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


def analyze_mood_and_intent(state: LeisureState):
    user_input = state.get("user_input", "")
    prompt = f"""
You are an intent extraction assistant.
From the user message below, extract:
- mood: their emotional state (e.g. sad, anxious, adventurous, bored, happy, lonely, stressed, tired, excited)
- genre: preferred fiction genre if mentioned (e.g. thriller, romance, fantasy, sci-fi). Empty string if none.
- author: preferred author if mentioned. Empty string if none.
- constraints: any other constraints (e.g. "short books", "ebooks only"). Empty string if none.

Respond ONLY with a valid JSON object. No explanation. No markdown.
Example: {{"mood": "sad", "genre": "romance", "author": "", "constraints": ""}}

User message: {user_input}
"""
    raw = llm.invoke([HumanMessage(content=prompt)]).content
    parsed = _parse_json_from_llm(raw)
    return {
        "mood":   parsed.get("mood", ""),
        "genre":  parsed.get("genre", ""),
        "author": parsed.get("author", ""),
    }


def build_search_query(state: LeisureState):
    mood_query = map_mood_to_query(state.get("mood", ""), content_type="leisure")
    genre      = state.get("genre", "")
    author     = state.get("author", "")

    parts = []
    if mood_query:
        parts.append(mood_query)
    if genre:
        parts.append(genre)
    if author:
        parts.append(f"author:{author}")
    parts.append("fiction")

    query = " ".join(parts) if parts else f"{state.get('user_input', '')} fiction"
    return {"search_query": query}


def tool_node(state: LeisureState):
    results = google_books_search.invoke({
        "query":       state.get("search_query", "fiction"),
        "max_results": 8
    })
    return {"tool_results": results}


def generate_response(state: LeisureState):
    system = SystemMessage(content=(
        "You are a warm, empathetic reading companion specializing in leisure fiction. "
        "Only recommend books from the provided candidates. Never invent titles."
    ))
    prompt = f"""
User request: {state.get("user_input", "")}
Detected mood: {state.get("mood", "not specified")}
Preferred genre: {state.get("genre", "not specified")}
Preferred author: {state.get("author", "not specified")}

Book candidates from Google Books:
{state.get("tool_results", [])}

Task:
- Pick the 3 best matches from the candidates above ONLY. Never invent books not in the list.
- For each book provide:
  * **Title** — Author(s)
  * 2-3 sentences explaining WHY this book fits the user's mood and request
  * Ebook: Yes/No based on isEbook field
  * 🔗 Link: use the best_link field from the candidate data. Always include it.
- Use a warm, supportive tone. Acknowledge the user's mood briefly at the start.
- NEVER recommend a book without a link.
"""
    resp = llm.invoke([system, HumanMessage(content=prompt)]).content
    return {"response": resp}


def build_leisure_agent():
    g = StateGraph(LeisureState)
    g.add_node("analyze", analyze_mood_and_intent)
    g.add_node("plan",    build_search_query)
    g.add_node("search",  tool_node)
    g.add_node("respond", generate_response)

    g.set_entry_point("analyze")
    g.add_edge("analyze", "plan")
    g.add_edge("plan",    "search")
    g.add_edge("search",  "respond")
    g.add_edge("respond", END)
    return g.compile()
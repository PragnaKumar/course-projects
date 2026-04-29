import re
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from models.llm import get_llm
from agents.leisure_agent import build_leisure_agent
from agents.research_agent import build_research_agent
from agents.tb_agent import build_tb_agent

llm = get_llm(temperature=0)

# Build sub-agents once at startup
leisure  = build_leisure_agent()
research = build_research_agent()
textbook = build_tb_agent()

VALID_ROUTES = {"leisure_books", "research_papers", "textbooks"}


class RouterState(TypedDict, total=False):
    user_input: str
    route:      str
    response:   str


def classify_route(state: RouterState):
    # Use .get() so a missing key never raises KeyError
    user_input = state.get("user_input", "")
    if not user_input:
        return {"route": "leisure_books"}

    prompt = f"""
Classify the user request into EXACTLY ONE of these categories:
- leisure_books    → fiction, novels, mood-based reading, audiobooks, ebooks
- research_papers  → academic papers, scientific articles, ArXiv, journals
- textbooks        → course textbooks, study materials, learning resources

Rules:
- Respond with ONLY the category string, nothing else.
- No punctuation, no quotes, no explanation.

User: {user_input}
"""
    raw   = llm.invoke([HumanMessage(content=prompt)]).content
    route = raw.strip().lower()
    route = re.sub(r"[\"'\.,]", "", route).strip()

    if route not in VALID_ROUTES:
        for valid in VALID_ROUTES:
            if valid in route:
                route = valid
                break
        else:
            route = "leisure_books"

    return {"route": route}


def run_leisure(state: RouterState):
    user_input = state.get("user_input", "")
    out = leisure.invoke({
        "user_input":   user_input,
        "mood":         "",
        "genre":        "",
        "author":       "",
        "search_query": "",
        "tool_results": [],
        "response":     ""
    })
    return {"response": out.get("response", "")}


def run_research(state: RouterState):
    user_input = state.get("user_input", "")
    out = research.invoke({
        "user_input":   user_input,
        "topic":        "",
        "keywords":     [],
        "date_filter":  "",
        "search_query": "",
        "tool_results": [],
        "response":     ""
    })
    return {"response": out.get("response", "")}


def run_textbooks(state: RouterState):
    user_input = state.get("user_input", "")
    out = textbook.invoke({
        "user_input":   user_input,
        "subject":      "",
        "level":        "",
        "author":       "",
        "search_query": "",
        "tool_results": [],
        "response":     ""
    })
    return {"response": out.get("response", "")}


def route_next(state: RouterState):
    return state.get("route", "leisure_books")


def build_router(memory=None):
    """
    Build and compile the router graph.

    Args:
        memory: Optional LangGraph SqliteSaver checkpointer for
                multi-turn conversation memory.
    """
    g = StateGraph(RouterState)
    g.add_node("classify",        classify_route)
    g.add_node("leisure_books",   run_leisure)
    g.add_node("research_papers", run_research)
    g.add_node("textbooks",       run_textbooks)

    g.set_entry_point("classify")
    g.add_conditional_edges(
        "classify",
        route_next,
        {
            "leisure_books":   "leisure_books",
            "research_papers": "research_papers",
            "textbooks":       "textbooks",
        }
    )

    g.add_edge("leisure_books",   END)
    g.add_edge("research_papers", END)
    g.add_edge("textbooks",       END)

    if memory:
        return g.compile(checkpointer=memory)
    return g.compile()
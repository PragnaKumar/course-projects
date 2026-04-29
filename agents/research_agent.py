"""
agents/research_agent.py

Research agent that searches ArXiv, PubMed and Semantic Scholar,
merges results, and always includes links in recommendations.
"""

import json
import re
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from models.llm import get_llm
from tools.arxiv import arxiv_search
from tools.pubmed import pubmed_search
from tools.biorxiv import biorxiv_search, medrxiv_search
from tools.ieee import ieee_search
from logic.mood_wrapper import map_mood_to_query

llm = get_llm(temperature=0.3)


class ResearchState(TypedDict, total=False):
    user_input:   str
    topic:        str
    keywords:     list
    date_filter:  str
    search_query: str
    tool_results: list
    response:     str


def _parse_json_from_llm(text: str) -> dict:
    try:
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return {}


def analyze_research_intent(state: ResearchState):
    user_input = state.get("user_input", "")
    prompt = f"""
You are a research intent extraction assistant.
From the user message below, extract:
- topic: the main research subject (e.g. "transformer neural networks")
- keywords: list of 3-5 specific technical keywords
- date_filter: year string if user mentions recent/latest (e.g. "2024"). Empty string if none.

Respond ONLY with valid JSON. No explanation. No markdown.
Example: {{"topic": "large language models", "keywords": ["LLM", "attention", "fine-tuning"], "date_filter": "2024"}}

User message: {user_input}
"""
    raw    = llm.invoke([HumanMessage(content=prompt)]).content
    parsed = _parse_json_from_llm(raw)
    return {
        "topic":       parsed.get("topic", user_input),
        "keywords":    parsed.get("keywords", []),
        "date_filter": parsed.get("date_filter", ""),
    }


def build_search_query(state: ResearchState):
    topic    = state.get("topic", state.get("user_input", ""))
    keywords = state.get("keywords", [])
    parts    = [topic] + keywords[:2]
    return {"search_query": " ".join(parts)}


def tool_node(state: ResearchState):
    """Search ArXiv, PubMed and Semantic Scholar, merge all results."""
    query       = state.get("search_query", "")
    date_filter = state.get("date_filter", "")
    all_results = []

    # ArXiv
    try:
        arxiv_results = arxiv_search.invoke({
            "query":       query,
            "max_results": 5,
            "date_filter": date_filter,
        })
        if arxiv_results and not arxiv_results[0].get("error"):
            all_results.extend(arxiv_results)
    except Exception:
        pass

    # PubMed (biomedical topics)
    try:
        pm_results = pubmed_search.invoke({
            "query":       query,
            "max_results": 3,
        })
        if pm_results and not pm_results[0].get("error"):
            all_results.extend(pm_results)
    except Exception:
        pass

    # bioRxiv (biology preprints)
    try:
        biorxiv_results = biorxiv_search.invoke({
            "query": query, "max_results": 3, "days_back": 60,
        })
        if biorxiv_results and not biorxiv_results[0].get("error"):
            all_results.extend(biorxiv_results)
    except Exception:
        pass

    # medRxiv (clinical medicine preprints)
    try:
        medrxiv_results = medrxiv_search.invoke({
            "query": query, "max_results": 3, "days_back": 60,
        })
        if medrxiv_results and not medrxiv_results[0].get("error"):
            all_results.extend(medrxiv_results)
    except Exception:
        pass

    # IEEE Xplore (engineering, CS, signal processing)
    try:
        ieee_results = ieee_search.invoke({
            "query": query, "max_results": 3,
        })
        if ieee_results and not ieee_results[0].get("error"):
            all_results.extend(ieee_results)
    except Exception:
        pass

    # Fallback message if everything failed
    if not all_results:
        all_results = [{"error": f"No results found for '{query}' across ArXiv, PubMed and Semantic Scholar."}]

    return {"tool_results": all_results}


def generate_response(state: ResearchState):
    system = SystemMessage(content=(
        "You are an academic research assistant. "
        "Recommend ONLY papers from the provided candidates list (ArXiv, Semantic Scholar, PubMed, bioRxiv, medRxiv). "
        "NEVER invent, fabricate or hallucinate paper titles, authors or links. "
        "If no suitable papers exist in the candidates, say so clearly — do not make papers up. "
        "ALWAYS include the full link for every paper you recommend."
    ))

    results = state.get("tool_results", [])

    # Check if all results are errors
    real_results = [r for r in results if not r.get("error")]

    if not real_results:
        return {"response": (
            "I couldn't find any papers matching your request across ArXiv, "
            "PubMed and Semantic Scholar. Please try rephrasing your query "
            "or using different keywords."
        )}

    prompt = f"""
User research request: {state.get("user_input", "")}
Extracted topic: {state.get("topic", "")}
Keywords: {state.get("keywords", [])}

Paper candidates from ArXiv, Semantic Scholar, PubMed, bioRxiv and medRxiv:
{json.dumps(real_results, indent=2)}

Task:
- Select the 3 most relevant papers from the candidates above ONLY.
- For each paper provide:
  * **Title** — Authors (Year if available) — Source (ArXiv/PubMed/Semantic Scholar)
  * 2-3 sentences explaining WHY this paper is relevant
  * 🔗 Link: [full URL from the candidates data]
- If a paper has no link in the data, skip it.
- Do NOT invent any papers not present in the candidates list.
- Keep the tone professional and helpful.
"""
    resp = llm.invoke([system, HumanMessage(content=prompt)]).content
    return {"response": resp}


def build_research_agent():
    g = StateGraph(ResearchState)
    g.add_node("analyze", analyze_research_intent)
    g.add_node("plan",    build_search_query)
    g.add_node("search",  tool_node)
    g.add_node("respond", generate_response)

    g.set_entry_point("analyze")
    g.add_edge("analyze", "plan")
    g.add_edge("plan",    "search")
    g.add_edge("search",  "respond")
    g.add_edge("respond", END)
    return g.compile()
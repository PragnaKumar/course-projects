"""
tools/arxiv.py

MCP client for the ArXiv MCP server.
Falls back to direct API call if MCP server is not running.
Includes proper User-Agent header to avoid 403 errors.
"""

import json
import urllib.parse
import urllib.request
import requests
from langchain.tools import tool

ARXIV_MCP_URL = "http://localhost:8001"
HEADERS = {"User-Agent": "Moodreads/1.0 (research recommender; python-requests)"}


def _call_mcp(tool_name: str, arguments: dict) -> list | None:
    """Try MCP server first. Returns None if server is not running."""
    try:
        r = requests.post(
            f"{ARXIV_MCP_URL}/call-tool",
            json={"name": tool_name, "arguments": arguments},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        return json.loads(data["content"][0]["text"])
    except requests.exceptions.ConnectionError:
        return None  # MCP server not running, fall back to direct call
    except Exception:
        return None


def _direct_arxiv_search(query: str, max_results: int, date_filter: str) -> list:
    """Direct ArXiv API call with proper headers."""
    query_encoded = urllib.parse.quote(query)
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query=all:{query_encoded}"
        f"&start=0&max_results={max_results}"
        f"&sortBy=submittedDate&sortOrder=descending"
    )

    try:
        req  = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
    except Exception as e:
        return [{"error": f"ArXiv request failed: {str(e)}"}]

    # Parse with feedparser
    import feedparser
    feed = feedparser.parse(content)

    if not feed.entries:
        return []

    results = []
    for entry in feed.entries:
        published = getattr(entry, "published", "")
        if date_filter and date_filter not in published:
            continue

        summary = getattr(entry, "summary", "")
        if len(summary) > 400:
            summary = summary[:400] + "..."

        link = entry.link
        results.append({
            "source":    "ArXiv",
            "title":     entry.title.replace("\n", " ").strip(),
            "authors":   [a.name for a in getattr(entry, "authors", [])],
            "summary":   summary.replace("\n", " ").strip(),
            "link":      link,
            "published": published,
            "arxiv_id":  link.split("/abs/")[-1] if "/abs/" in link else "",
        })

    return results


@tool
def arxiv_search(query: str, max_results: int = 5, date_filter: str = "") -> list:
    """
    Search ArXiv for academic papers.
    Returns title, authors, summary, link, published date and arxiv_id.
    Each result includes a direct link to the paper.
    """
    # Try MCP server first
    mcp_result = _call_mcp("arxiv_search", {
        "query": query, "max_results": max_results, "date_filter": date_filter
    })
    if mcp_result is not None:
        return mcp_result

    # Fall back to direct API call
    return _direct_arxiv_search(query, max_results, date_filter)
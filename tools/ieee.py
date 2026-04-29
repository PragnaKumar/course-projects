"""
tools/ieee.py

MCP client for the IEEE Xplore MCP server.
Falls back to direct API call if MCP server is not running.
Requires IEEE_API_KEY in your .env file.
"""

import os
import json
import urllib.parse
import urllib.request
import requests
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

IEEE_MCP_URL  = "http://localhost:8003"
IEEE_API_KEY  = os.environ.get("IEEE_API_KEY", "")
API_URL       = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
HEADERS       = {"User-Agent": "Moodreads/1.0 (research recommender; python-requests)"}


def _call_mcp(tool_name: str, arguments: dict) -> list | None:
    """Try MCP server first. Returns None if server is not running."""
    try:
        r = requests.post(
            f"{IEEE_MCP_URL}/call-tool",
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


def _direct_ieee_search(query: str, max_results: int) -> list:
    """Direct IEEE Xplore API call — used when MCP server is not running."""
    if not IEEE_API_KEY:
        return [{"error": (
            "IEEE API key not configured. "
            "Add IEEE_API_KEY=your_key to your .env file. "
            "Get a free key at developer.ieee.org"
        )}]

    params = urllib.parse.urlencode({
        "querytext":    query,
        "max_records":  min(max_results, 25),
        "start_record": 1,
        "sort_order":   "desc",
        "sort_field":   "article_number",
        "apikey":       IEEE_API_KEY,
    })

    try:
        req = urllib.request.Request(f"{API_URL}?{params}", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return [{"error": "IEEE API key is invalid or expired. Check IEEE_API_KEY in .env."}]
        return [{"error": f"IEEE API error: {e.code} {e.reason}"}]
    except Exception as e:
        return [{"error": f"IEEE request failed: {str(e)}"}]

    articles = data.get("articles", [])
    if not articles:
        return []

    results = []
    for a in articles:
        abstract = a.get("abstract", "")
        if len(abstract) > 400:
            abstract = abstract[:400] + "..."

        authors_data = a.get("authors", {}).get("authors", [])
        authors      = [auth.get("full_name", "") for auth in authors_data[:5]]

        article_number = a.get("article_number", "")
        link = (
            a.get("html_url") or
            (f"https://ieeexplore.ieee.org/document/{article_number}" if article_number else "")
        )

        results.append({
            "source":      "IEEE Xplore",
            "title":       a.get("title", ""),
            "authors":     authors,
            "summary":     abstract,
            "published":   str(a.get("publication_year", "")),
            "publication": a.get("publication_title", ""),
            "doi":         a.get("doi", ""),
            "link":        link,
            "pdf_link":    a.get("pdf_url", ""),
            "open_access": a.get("access_type", "") == "OPEN_ACCESS",
        })

    return results


@tool
def ieee_search(query: str, max_results: int = 5) -> list:
    """
    Search IEEE Xplore for journal articles, conference papers and standards via MCP server.
    Best for electrical engineering, CS, signal processing, robotics and communications.
    Returns title, authors, abstract, publication, year, DOI and direct IEEE Xplore link.
    """
    # Try MCP server first
    mcp_result = _call_mcp("ieee_search", {
        "query": query, "max_results": max_results
    })
    if mcp_result is not None:
        return mcp_result

    # Fall back to direct API call
    return _direct_ieee_search(query, max_results)
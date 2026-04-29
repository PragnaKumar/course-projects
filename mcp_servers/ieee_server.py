"""
mcp_servers/ieee_server.py

FastMCP HTTP/SSE server wrapping the IEEE Xplore Metadata API.
Run independently:  python mcp_servers/ieee_server.py
Listens on:         http://localhost:8003

Requires IEEE_API_KEY in your .env file.
Get a free key at: developer.ieee.org
"""

import os
import json
import urllib.parse
import urllib.request
import uvicorn
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("ieee-server")

HEADERS      = {"User-Agent": "Moodreads/1.0 (research recommender; python-requests)"}
IEEE_API_KEY = os.environ.get("IEEE_API_KEY", "")
API_URL      = "https://ieeexploreapi.ieee.org/api/v1/search/articles"


@mcp.tool()
def ieee_search(query: str, max_results: int = 5) -> list:
    """
    Search IEEE Xplore for journal articles, conference papers and standards.
    Best for electrical engineering, CS, signal processing, robotics and communications.
    Returns title, authors, abstract, publication, year, DOI and direct IEEE Xplore link.

    Args:
        query:       Search query string.
        max_results: Maximum number of results to return (default 5, max 25).

    Returns:
        List of dicts with title, authors, summary, published, publication,
        doi, link, pdf_link, open_access, source fields.
    """
    if not IEEE_API_KEY:
        return [{"error": (
            "IEEE API key not configured. "
            "Get a free key at developer.ieee.org and add "
            "IEEE_API_KEY=your_key to your .env file."
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
        req = urllib.request.Request(
            f"{API_URL}?{params}",
            headers=HEADERS
        )
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


if __name__ == "__main__":
    if not IEEE_API_KEY:
        print("⚠️  WARNING: IEEE_API_KEY not found in .env — searches will return an error.")
        print("   Get a free key at: developer.ieee.org")
    else:
        print(f"✅ IEEE API key loaded ({IEEE_API_KEY[:6]}...)")
    print("Starting IEEE Xplore MCP server on http://localhost:8003")
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=8003)
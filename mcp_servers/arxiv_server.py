"""
mcp_servers/arxiv_server.py

FastMCP HTTP/SSE server wrapping the ArXiv API.
Run independently:  python mcp_servers/arxiv_server.py
Listens on:         http://localhost:8001
"""

import feedparser
import urllib.parse
import uvicorn
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("arxiv-server")


@mcp.tool()
def arxiv_search(query: str, max_results: int = 5, date_filter: str = "") -> list:
    """
    Search ArXiv and return paper metadata.

    Args:
        query:       Search query string.
        max_results: Maximum number of results to return (default 5).
        date_filter: Optional year string to filter by (e.g. "2024").

    Returns:
        List of dicts with title, authors, summary, link, published, arxiv_id.
    """
    query_encoded = urllib.parse.quote(query)

    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query=all:{query_encoded}"
        f"&start=0"
        f"&max_results={max_results}"
        f"&sortBy=submittedDate&sortOrder=descending"
    )

    try:
        import urllib.request
        headers = {"User-Agent": "Moodreads/1.0 (research recommender; python-requests)"}
        req  = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
        feed = feedparser.parse(content)
    except Exception as e:
        return [{"error": f"ArXiv request failed: {str(e)}"}]

    if not feed.entries:
        return [{"error": "No results found on ArXiv for this query."}]

    results = []
    for entry in feed.entries:
        published = getattr(entry, "published", "")

        if date_filter and date_filter not in published:
            continue

        summary = getattr(entry, "summary", "")
        if len(summary) > 400:
            summary = summary[:400] + "..."

        results.append({
            "title":     entry.title.replace("\n", " ").strip(),
            "authors":   [a.name for a in getattr(entry, "authors", [])],
            "summary":   summary.replace("\n", " ").strip(),
            "link":      entry.link,
            "published": published,
            "arxiv_id":  entry.link.split("/abs/")[-1] if "/abs/" in entry.link else "",
        })

    if not results:
        return [{"error": f"No ArXiv results matched the date filter '{date_filter}'."}]

    return results


if __name__ == "__main__":
    print("Starting ArXiv MCP server on http://localhost:8001")
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=8001)
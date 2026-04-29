import urllib.parse
"""
mcp_servers/google_books_server.py

FastMCP HTTP/SSE server wrapping the Google Books API.
Run independently:  python mcp_servers/google_books_server.py
Listens on:         http://localhost:8002
"""

import os
import requests
import uvicorn
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("google-books-server")

GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")


@mcp.tool()
def google_books_search(query: str, max_results: int = 8) -> list:
    """
    Search Google Books for books, textbooks and ebooks.

    Args:
        query:       Search query string.
        max_results: Maximum number of results (default 8, max 40).

    Returns:
        List of dicts with title, authors, description, categories,
        publisher, publishedDate, pageCount, isEbook, previewLink, infoLink.
    """
    url    = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q":          query,
        "maxResults": min(max_results, 40),
        "printType":  "books",
        "langRestrict": "en",
    }
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY

    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.Timeout:
        return [{"error": "Google Books request timed out."}]
    except requests.exceptions.HTTPError as e:
        return [{"error": f"Google Books API error: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Unexpected error: {str(e)}"}]

    items = data.get("items", [])
    if not items:
        return [{"error": "No results found on Google Books for this query."}]

    out = []
    for item in items:
        info   = item.get("volumeInfo", {})
        access = item.get("accessInfo", {})

        description = info.get("description", "")
        if len(description) > 400:
            description = description[:400] + "..."

        out.append({
            "title":         info.get("title", "Unknown Title"),
            "authors":       info.get("authors", ["Unknown Author"]),
            "categories":    info.get("categories", []),
            "description":   description,
            "publishedDate": info.get("publishedDate", ""),
            "pageCount":     info.get("pageCount", None),
            "language":      info.get("language", ""),
            "publisher":     info.get("publisher", ""),
            "previewLink":   info.get("previewLink", ""),
            "infoLink":      info.get("infoLink", ""),
            "best_link": (
                info.get("infoLink") or
                info.get("previewLink") or
                "https://books.google.com/books?q=" + urllib.parse.quote(info.get("title", ""))
            ),
            "isEbook": (
                access.get("epub", {}).get("isAvailable", False) or
                access.get("pdf",  {}).get("isAvailable", False)
            ),
        })

    return out


if __name__ == "__main__":
    print("Starting Google Books MCP server on http://localhost:8002")
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=8002)
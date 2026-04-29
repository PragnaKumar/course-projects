"""
tools/google_books.py

MCP client for the Google Books MCP server.
Agents call google_books_search exactly as before — the MCP layer is transparent.
"""

import json
import requests
from langchain.tools import tool

GOOGLE_BOOKS_MCP_URL = "http://localhost:8002"


def _call_mcp(tool_name: str, arguments: dict) -> list:
    """Send a tool call request to the MCP server and return the result."""
    try:
        r = requests.post(
            f"{GOOGLE_BOOKS_MCP_URL}/call-tool",
            json={"name": tool_name, "arguments": arguments},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        # MCP returns {"content": [{"type": "text", "text": "..."}]}
        return json.loads(data["content"][0]["text"])
    except requests.exceptions.ConnectionError:
        return [{"error": "Google Books MCP server is not running. Start it with: python mcp_servers/google_books_server.py"}]
    except requests.exceptions.Timeout:
        return [{"error": "Google Books MCP server timed out."}]
    except Exception as e:
        return [{"error": f"MCP call failed: {str(e)}"}]


@tool
def google_books_search(query: str, max_results: int = 8) -> list:
    """
    Search Google Books for books, textbooks and ebooks via MCP server.
    Returns title, authors, description, categories, publisher and ebook availability.
    """
    return _call_mcp("google_books_search", {
        "query":       query,
        "max_results": max_results,
    })
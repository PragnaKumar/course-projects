"""
tools/biorxiv.py

bioRxiv + medRxiv search tool.

Important API note: The bioRxiv/medRxiv API does NOT support keyword search.
It only returns papers by date range. We fetch recent papers and filter
locally by keyword match against title + abstract.

No API key required. Free and open.
Covers: biology, neuroscience, genomics, ecology, clinical medicine (medRxiv).
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from langchain.tools import tool

HEADERS  = {"User-Agent": "Moodreads/1.0 (research recommender; python-requests)"}
BASE_URL = "https://api.biorxiv.org/details"


def _fetch_papers(server: str, days_back: int = 30, cursor: int = 0) -> list:
    """
    Fetch recent papers from bioRxiv or medRxiv within the last N days.

    Args:
        server:    'biorxiv' or 'medrxiv'
        days_back: How many days back to search (default 30)
        cursor:    Pagination start (default 0)

    Returns:
        List of raw paper dicts from the API.
    """
    end_date   = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    url = f"{BASE_URL}/{server}/{start_date}/{end_date}/{cursor}/json"

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("collection", [])
    except Exception as e:
        return []


def _keyword_match(paper: dict, keywords: list) -> bool:
    """Check if any keyword appears in the paper's title or abstract."""
    text = (
        (paper.get("title", "") + " " + paper.get("abstract", ""))
        .lower()
    )
    return any(kw.lower() in text for kw in keywords)


def _format_paper(paper: dict, server: str) -> dict:
    """Format a raw API paper dict into a clean result dict."""
    doi      = paper.get("doi", "")
    abstract = paper.get("abstract", "")
    if len(abstract) > 400:
        abstract = abstract[:400] + "..."

    return {
        "source":    "bioRxiv" if server == "biorxiv" else "medRxiv",
        "title":     paper.get("title", "").strip(),
        "authors":   paper.get("authors", "").split("; ")[:5],
        "summary":   abstract.strip(),
        "published": paper.get("date", ""),
        "category":  paper.get("category", ""),
        "doi":       doi,
        "link":      f"https://www.biorxiv.org/content/{doi}" if doi else "",
        "pdf_link":  f"https://www.biorxiv.org/content/{doi}.full.pdf" if doi else "",
    }


@tool
def biorxiv_search(query: str, max_results: int = 5, days_back: int = 60) -> list:
    """
    Search bioRxiv for recent biology and life science preprints.
    Covers neuroscience, genomics, ecology, bioinformatics, cell biology and more.
    Returns title, authors, abstract, category, DOI and direct link.

    Args:
        query:       Search query — keywords to match in title/abstract.
        max_results: Maximum results to return (default 5).
        days_back:   How many days back to search (default 60).
    """
    keywords = query.strip().split()
    papers   = _fetch_papers("biorxiv", days_back=days_back)

    if not papers:
        return [{"error": "Could not reach bioRxiv API. Check your connection."}]

    matched = [
        _format_paper(p, "biorxiv")
        for p in papers
        if _keyword_match(p, keywords)
    ]

    if not matched:
        # Widen search window and try again
        papers = _fetch_papers("biorxiv", days_back=days_back * 2)
        matched = [
            _format_paper(p, "biorxiv")
            for p in papers
            if _keyword_match(p, keywords)
        ]

    return matched[:max_results] if matched else []


@tool
def medrxiv_search(query: str, max_results: int = 5, days_back: int = 60) -> list:
    """
    Search medRxiv for recent clinical medicine and health science preprints.
    Covers epidemiology, clinical trials, public health, psychiatry and more.
    Returns title, authors, abstract, category, DOI and direct link.

    Args:
        query:       Search query — keywords to match in title/abstract.
        max_results: Maximum results to return (default 5).
        days_back:   How many days back to search (default 60).
    """
    keywords = query.strip().split()
    papers   = _fetch_papers("medrxiv", days_back=days_back)

    if not papers:
        return [{"error": "Could not reach medRxiv API. Check your connection."}]

    matched = [
        _format_paper(p, "medrxiv")
        for p in papers
        if _keyword_match(p, keywords)
    ]

    if not matched:
        papers  = _fetch_papers("medrxiv", days_back=days_back * 2)
        matched = [
            _format_paper(p, "medrxiv")
            for p in papers
            if _keyword_match(p, keywords)
        ]

    return matched[:max_results] if matched else []
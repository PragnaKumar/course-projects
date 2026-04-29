"""
tools/pubmed.py

PubMed search tool using NCBI E-utilities API (free, no API key required).
Returns paper metadata including direct PubMed links.
"""

import urllib.parse
import urllib.request
import json
from langchain.tools import tool

HEADERS      = {"User-Agent": "Moodreads/1.0 (research recommender; python-requests)"}
ESEARCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def _fetch(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None


@tool
def pubmed_search(query: str, max_results: int = 5) -> list:
    """
    Search PubMed for biomedical and life science research papers.
    Returns title, authors, abstract snippet, journal, published date and link.
    Each result includes a direct PubMed link.
    """
    # Step 1: search for IDs
    search_params = urllib.parse.urlencode({
        "db":      "pubmed",
        "term":    query,
        "retmax":  max_results,
        "retmode": "json",
        "sort":    "relevance",
    })
    search_data = _fetch(f"{ESEARCH_URL}?{search_params}")

    if not search_data:
        return [{"error": "PubMed search request failed."}]

    ids = search_data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    # Step 2: fetch summaries for those IDs
    summary_params = urllib.parse.urlencode({
        "db":      "pubmed",
        "id":      ",".join(ids),
        "retmode": "json",
    })
    summary_data = _fetch(f"{ESUMMARY_URL}?{summary_params}")

    if not summary_data:
        return [{"error": "PubMed summary request failed."}]

    results = []
    uids    = summary_data.get("result", {}).get("uids", [])

    for uid in uids:
        paper = summary_data["result"].get(uid, {})
        if not paper:
            continue

        # Extract authors
        authors = [
            a.get("name", "") for a in paper.get("authors", [])
            if a.get("authtype") == "Author"
        ][:5]  # cap at 5 authors

        # Published date
        pub_date = paper.get("pubdate", "") or paper.get("epubdate", "")

        results.append({
            "source":    "PubMed",
            "title":     paper.get("title", "").rstrip("."),
            "authors":   authors,
            "summary":   paper.get("sorttitle", ""),   # short description
            "journal":   paper.get("source", ""),
            "published": pub_date,
            "link":      f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
            "pubmed_id": uid,
        })

    return results
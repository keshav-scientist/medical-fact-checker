"""
pubmed_retrieval.py

Stage 2 of the pipeline. Pulls real, citable evidence from PubMed
BEFORE the model writes anything. Uses NCBI's free E-utilities API.

Docs: https://www.ncbi.nlm.nih.gov/books/NBK25501/
No API key required for light use (~3 requests/second).
"""

import time
import requests
from dataclasses import dataclass
from typing import List

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# NCBI asks that you identify your tool and give a contact email so
# they can reach you about unusual traffic. Not enforced, but good
# practice - replace with your own.
TOOL_NAME = "medical-fact-checker"
CONTACT_EMAIL = "your-email@example.com"


@dataclass
class Evidence:
    pmid: str
    title: str
    abstract: str

    def as_citation(self) -> str:
        return f"[PMID {self.pmid}] {self.title}"


def search_pubmed(query: str, max_results: int = 5) -> List[str]:
    """Return a list of PubMed IDs relevant to the query."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "sort": "relevance",
        "tool": TOOL_NAME,
        "email": CONTACT_EMAIL,
    }
    resp = requests.get(ESEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("esearchresult", {}).get("idlist", [])


def fetch_abstracts(pmids: List[str]) -> List[Evidence]:
    """Fetch title + abstract text for a list of PubMed IDs."""
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "text",
        "tool": TOOL_NAME,
        "email": CONTACT_EMAIL,
    }
    resp = requests.get(EFETCH_URL, params=params, timeout=15)
    resp.raise_for_status()

    # E-utils returns plain-text records separated by blank lines.
    # This is a simple splitter - good enough for a prototype. For
    # production, request retmode="xml" and parse it properly instead
    # of relying on blank-line splitting, which occasionally misfires
    # on records with unusual formatting.
    records = [r for r in resp.text.strip().split("\n\n\n") if r.strip()]
    evidence = []
    for pmid, record in zip(pmids, records):
        lines = [l for l in record.strip().split("\n") if l.strip()]
        title = lines[1] if len(lines) > 1 else "(title unavailable)"
        abstract = " ".join(lines[2:]) if len(lines) > 2 else record.strip()
        evidence.append(Evidence(pmid=pmid, title=title, abstract=abstract[:1500]))
    return evidence


def retrieve_evidence(claim: str, max_results: int = 5) -> List[Evidence]:
    """Full retrieval step: claim -> list of Evidence with citations."""
    pmids = search_pubmed(claim, max_results=max_results)
    time.sleep(0.34)  # stay under NCBI's ~3 req/sec limit without a key
    return fetch_abstracts(pmids)

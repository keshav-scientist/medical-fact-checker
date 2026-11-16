"""
medlineplus_retrieval.py

Second evidence source: MedlinePlus, also run by the National Library
of Medicine (same organization behind PubMed). MedlinePlus is written
in plain language for the public, which complements PubMed abstracts -
those are written for researchers and can be hard to ground a
consumer-facing answer in on their own.

Docs: https://medlineplus.gov/about/developers/webservices/
Free, no API key. Be polite: NLM asks for no more than 85 requests
per minute per IP, and recommends caching results for 12-24 hours.
"""

from gettext import install
import xml.etree.ElementTree as ET
from typing import List

import requests

from evidence import Evidence

BASE_URL = "https://wsearch.nlm.nih.gov/ws/query"
TOOL_NAME = "medical-fact-checker"
CONTACT_EMAIL = "your-email@example.com"


def _text(content_el) -> str:
    """Pull all text out of a <content> element, stripping the
    <span class="qt..."> highlight tags MedlinePlus wraps matches in."""
    return " ".join(t.strip() for t in content_el.itertext() if t.strip())


def _parse_response(xml_bytes: bytes) -> List[Evidence]:
    """Parse a MedlinePlus Web service XML response into Evidence
    objects. Split out from retrieve_evidence() so it can be unit
    tested without a network call - see the __main__ block below."""
    root = ET.fromstring(xml_bytes)
    evidence = []
    for doc in root.findall(".//document"):
        url = doc.get("url", "")
        title = "(title unavailable)"
        full_summary, snippet = None, None
        for content in doc.findall("content"):
            name = content.get("name")
            if name == "title":
                title = _text(content)
            elif name == "FullSummary":
                full_summary = _text(content)
            elif name == "snippet":
                snippet = _text(content)
        text = full_summary or snippet or ""
        evidence.append(
            Evidence(
                source="MedlinePlus",
                citation_id=url,
                title=title,
                text=text[:1500],
                url=url,
            )
        )
    return evidence


def retrieve_evidence(claim: str, max_results: int = 3) -> List[Evidence]:
    """Full retrieval step: claim -> list of Evidence from MedlinePlus."""
    params = {
        "db": "healthTopics",
        "term": claim,
        "retmax": max_results,
        "rettype": "brief",
        "tool": TOOL_NAME,
        "email": CONTACT_EMAIL,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    return _parse_response(resp.content)


if __name__ == "__main__":
    # Quick offline sanity check using a real example response body
    # taken from MedlinePlus's own API documentation - lets you verify
    # the parser without hitting the network.
    SAMPLE_XML = b"""<?xml version="1.0"?>
    <nlmSearchResult>
      <list>
        <document rank="0" url="https://medlineplus.gov/diabetesmedicines.html">
          <content name="title"><span class="qt0">Diabetes</span> <span class="qt1">Medicines</span></content>
          <content name="organizationName">National Library of Medicine</content>
          <content name="FullSummary"><p><span class="qt0">Diabetes</span> means your blood glucose is too high. With Type 1 diabetes, your pancreas does not make insulin.</p></content>
          <content name="snippet">... food choices and physical activity, you may need diabetes medicines ...</content>
        </document>
      </list>
    </nlmSearchResult>"""
    results = _parse_response(SAMPLE_XML)
    for e in results:
        print(e.as_citation())
        print(e.text)

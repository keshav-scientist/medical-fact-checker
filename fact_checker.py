"""
fact_checker.py

Ties safety_filter + pubmed_retrieval + the Claude API together into
one fact-checking call. The model is never allowed to answer from its
own memory alone - it must ground its answer in the retrieved
abstracts, and it must say so plainly if there isn't enough evidence.
"""

import json
from dataclasses import dataclass, field
from typing import List

import anthropic

import safety_filter
from pubmed_retrieval import retrieve_evidence, Evidence

# "claude-haiku-4-5" is a cheaper/faster swap while you're testing.
MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You are a careful medical fact-checking assistant.



@dataclass
class FactCheckResult:
    verdict: str
    confidence: str
    explanation: str
    cited_pmids: List[str]
    disclaimer: str
    sources: List[Evidence] = field(default_factory=list)


@dataclass
class BlockedResult:
    reason: str
    message: str


def _build_user_message(claim: str, evidence: List[Evidence]) -> str:
    if not evidence:
        return (
            f"Claim to check: {claim}\n\n"
            "No relevant evidence was found in PubMed for this claim. "
            "You must return verdict='insufficient evidence'."
        )
    blocks = "\n\n".join(
        f"[PMID {e.pmid}] {e.title}\n{e.abstract}" for e in evidence
    )
    return f"Claim to check: {claim}\n\nEvidence excerpts:\n\n{blocks}"


def check_claim(claim: str):
    """Run the full pipeline: safety -> retrieval -> grounded verdict.

    Returns a FactCheckResult on success, or a BlockedResult if the
    safety filter stopped it before it ever reached the model.
    """
    safety = safety_filter.check(claim)
    if not safety.allowed:
        return BlockedResult(reason=safety.reason, message=safety.message)

    evidence = retrieve_evidence(claim)

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_message(claim, evidence)}],
    )

    raw_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        # Model didn't return clean JSON - fail safe rather than guess.
        return FactCheckResult(
            verdict="insufficient evidence",
            confidence="low",
            explanation="The model's response couldn't be parsed reliably.",
            cited_pmids=[],
            disclaimer="This is not medical advice. Please consult a doctor.",
            sources=evidence,
        )

    return FactCheckResult(
        verdict=parsed.get("verdict", "insufficient evidence"),
        confidence=parsed.get("confidence", "low"),
        explanation=parsed.get("explanation", ""),
        cited_pmids=parsed.get("cited_pmids", []),
        disclaimer=parsed.get(
            "disclaimer", "This is not medical advice. Please consult a doctor."
        ),
        sources=evidence,
    )
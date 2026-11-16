"""
safety_filter.py

Stage 1 of the pipeline. Runs BEFORE retrieval or any AI call.
Blocks / redirects three categories of unsafe requests:

  1. Emergencies (chest pain, suicidal ideation, severe bleeding, etc.)
  2. Requests for a personal diagnosis ("do I have X")
  3. Requests for dosage / drug-interaction instructions

This is deliberately simple keyword/regex matching, not an ML
classifier. For a safety gate, simple and auditable beats clever
and opaque - you can read every rule in this file in under a minute.
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SafetyResult:
    allowed: bool
    reason: Optional[str] = None
    message: Optional[str] = None


EMERGENCY_PATTERNS = [
    r"\bchest pain\b",
    r"\bcan'?t breathe\b",
    r"\bcannot breathe\b",
    r"\bsevere bleeding\b",
    r"\bheart attack\b",
    r"\bstroke\b",
    r"\bsuicid\w*\b",
    r"\bkill myself\b",
    r"\boverdose\b",
    r"\bunconscious\b",
    r"\bnot breathing\b",
    r"\banaphyla\w*\b",
]

DIAGNOSIS_PATTERNS = [
    r"\bdo i have\b",
    r"\bam i (having|experiencing)\b",
    r"\bwhat'?s wrong with me\b",
    r"\bdiagnose me\b",
    r"\bwhat disease do i\b",
]

DOSAGE_PATTERNS = [
    r"\bhow many (mg|milligrams|pills|tablets)\b",
    r"\bhow much (should i take|to take)\b",
    r"\bwhat dose\b",
    r"\bcan i mix\b.*\bwith\b",
    r"\bdosage of\b",
]

EMERGENCY_MESSAGE = (
    "This sounds like it could be a medical emergency. I can't help with "
    "that here - please call your local emergency number right now "
    "(911 in the US, 112 in the EU, or your country's equivalent), or go "
    "to the nearest emergency room."
)

DIAGNOSIS_MESSAGE = (
    "I can't diagnose a personal symptom or tell you what's wrong with you "
    "- that needs an actual clinician who can examine you and see your "
    "history. I can fact-check general medical claims instead. Try "
    "rephrasing as a general claim, e.g. 'is it true that fever always "
    "means infection?'"
)

DOSAGE_MESSAGE = (
    "I can't give dosing or drug-interaction instructions - getting that "
    "wrong can be dangerous, and it depends on your specific health "
    "history. Please ask a pharmacist or your doctor, or call a poison "
    "control line if this is urgent."
)


def _matches_any(text: str, patterns: List[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def check(text: str) -> SafetyResult:
    """Run a query through the safety gate before it reaches retrieval
    or the model. Returns SafetyResult(allowed=False, ...) if blocked."""
    if _matches_any(text, EMERGENCY_PATTERNS):
        return SafetyResult(False, "emergency", EMERGENCY_MESSAGE)
    if _matches_any(text, DIAGNOSIS_PATTERNS):
        return SafetyResult(False, "diagnosis_request", DIAGNOSIS_MESSAGE)
    if _matches_any(text, DOSAGE_PATTERNS):
        return SafetyResult(False, "dosage_request", DOSAGE_MESSAGE)
    return SafetyResult(True)

from __future__ import annotations

import re
from typing import Iterable

CITATION_RE = re.compile(r"\[(F\d{3})\]")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
INJECTION_PATTERNS = [
    r"ignore (the )?(previous|above|system|developer|knowledge)",
    r"no citations needed",
    r"without citations",
    r"pretend",
    r"override",
    r"disregard",
]

def extract_citation_ids(text: str) -> list[str]:
    return CITATION_RE.findall(text or "")

def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_RE.split(text or "") if s.strip()]

def detect_prompt_injection(text: str) -> list[str]:
    lowered = (text or "").lower()
    return [pattern for pattern in INJECTION_PATTERNS if re.search(pattern, lowered)]

def is_abstention(text: str) -> bool:
    lowered = (text or "").lower()
    cues = ["not enough", "cannot answer", "can't answer", "do not have", "don't have", "not supported", "abstain"]
    return any(cue in lowered for cue in cues)

def factual_sentence_without_citation(sentence: str) -> bool:
    if extract_citation_ids(sentence) or is_abstention(sentence):
        return False
    words = sentence.split()
    has_number = any(ch.isdigit() for ch in sentence)
    has_capitalized = sum(1 for w in words if w[:1].isupper()) >= 2
    return len(words) >= 6 and (has_number or has_capitalized)

def unsupported_sentences(answer: str, valid_fact_ids: Iterable[str]) -> list[str]:
    valid = set(valid_fact_ids)
    unsupported = []
    for sentence in split_sentences(answer):
        citations = set(extract_citation_ids(sentence))
        if factual_sentence_without_citation(sentence):
            unsupported.append(sentence)
        elif citations and not citations.issubset(valid):
            unsupported.append(sentence)
    return unsupported

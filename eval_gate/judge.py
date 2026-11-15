"""Rubric judge for retrieval QA answers.

The default judge is DETERMINISTIC and works offline: it scores an answer
against the case's gold facts (must be present) and distractors (must be
absent) using normalized text matching. No model call, no API key, so the
CI gate can run on every pull request.

Rubric (each dimension 0-2, case total 0-6):
- groundedness: share of gold facts found in the answer
    2 = all gold facts present, 1 = at least half, 0 = fewer than half
- relevance: overlap between the question's content words and the answer
    2 = >= 50% of question words appear, 1 = >= 25%, 0 = below 25%
- accuracy: the answer must not state anything known-wrong
    2 = no distractor present, 0 = a distractor is present (wrong fact)
    or the answer is empty. Accuracy is deliberately binary: it answers
    one question -- did the system state something false? Brevity is
    already covered by groundedness and relevance, so a short correct
    answer is not punished here.

A case PASSES when total >= 4 and accuracy == 2. A case with a matched
distractor is a CRITICAL failure: it states a wrong fact.
"""

from __future__ import annotations

import re
import unicodedata

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "do", "does", "did",
    "which", "what", "who", "how", "many", "much", "in", "on", "at",
    "of", "to", "for", "by", "and", "or", "there", "it", "its", "be",
    "book", "books", "called", "have", "has", "did", "does", "than",
}

MIN_CASE_SCORE = 4  # pass threshold per case, out of 6


def normalize(text: str) -> str:
    """Lowercase, strip accents/punctuation, collapse whitespace.

    A "." is kept only when it is a decimal point (followed by a digit);
    sentence-final periods are dropped so "$24.50." normalizes to "$24.50".
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"\.(?!\d)", " ", text)
    text = re.sub(r"[^a-z0-9$%.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _content_words(text: str) -> set[str]:
    return {w for w in normalize(text).split() if w not in STOPWORDS}


def fact_present(fact: str, answer: str) -> bool:
    """True when the fact's normalized form appears in the answer.

    Numbers are matched as whole words so that e.g. gold fact "2" cannot
    match the "2" inside "2022" or "$24.50". Single-word facts match on
    word boundaries so "a" cannot match the "a" inside "matches".
    Multi-word facts match as phrases.
    """
    fact_n, answer_n = normalize(fact), normalize(answer)
    if re.fullmatch(r"[\d$%.]+", fact_n):
        return re.search(rf"(?<![\d.]){re.escape(fact_n)}(?![\d.])",
                         answer_n) is not None
    if " " not in fact_n:
        return re.search(rf"\b{re.escape(fact_n)}\b", answer_n) is not None
    return fact_n in answer_n


def score_groundedness(gold_facts: list[str], answer: str) -> int:
    if not gold_facts:
        return 2
    found = sum(1 for f in gold_facts if fact_present(f, answer))
    share = found / len(gold_facts)
    if share >= 1.0:
        return 2
    if share >= 0.5:
        return 1
    return 0


def score_relevance(question: str, answer: str) -> int:
    words = _content_words(question)
    if not words:
        return 2
    answer_words = set(normalize(answer).split())
    overlap = len(words & answer_words) / len(words)
    if overlap >= 0.5:
        return 2
    if overlap >= 0.25:
        return 1
    return 0


def score_accuracy(distractors: list[str], answer: str) -> tuple[int, list[str]]:
    """Returns (score, matched distractors). Binary by design: 2 = no wrong
    fact stated, 0 = a distractor is present or the answer is empty."""
    if not normalize(answer):
        return 0, []
    matched = [d for d in distractors if fact_present(d, answer)]
    if matched:
        return 0, matched
    return 2, []


def score_case(case: dict, answer: str) -> dict:
    """Score one eval case. Returns a result dict with per-dimension scores."""
    groundedness = score_groundedness(case.get("gold_facts", []), answer)
    relevance = score_relevance(case["question"], answer)
    accuracy, matched = score_accuracy(case.get("distractors", []), answer)
    total = groundedness + relevance + accuracy
    passed = total >= MIN_CASE_SCORE and accuracy == 2
    return {
        "id": case["id"],
        "question": case["question"],
        "answer": answer,
        "groundedness": groundedness,
        "relevance": relevance,
        "accuracy": accuracy,
        "total": total,
        "passed": passed,
        "critical": bool(matched),  # stated a known-wrong fact
        "matched_distractors": matched,
    }

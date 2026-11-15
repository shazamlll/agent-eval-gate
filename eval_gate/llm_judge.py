"""LLM-as-judge adapter (NOT wired up by default).

This module exists to show the shape of a model-based judge: same rubric
as the deterministic judge in judge.py, but the scores come from an LLM
instead of string matching. It is deliberately OFF by default:

- the runner only uses it when called with --judge llm
- it needs an API key in the environment (GEMINI_API_KEY or OPENAI_API_KEY)
- it has never been run against a real model in this repo; the prompt and
  the response parsing are untested against live endpoints

Do not treat this as a working integration. Wiring it up (pick a cheap
model, e.g. a Gemini flash-tier model, set the key, run it, and compare its
agreement with the deterministic judge on this same eval set) is listed
under "Remaining work" in the README.
"""

from __future__ import annotations

import json
import os
import urllib.request

RUBRIC_PROMPT = """You are an evaluator for a bookstore question-answering system.
Score the ANSWER against the QUESTION using this rubric. Reply with JSON only.

groundedness (0-2): how many of the GOLD FACTS does the answer state?
  2 = all, 1 = at least half, 0 = fewer than half.
relevance (0-2): does the answer address the QUESTION?
  2 = directly answers it, 1 = partially related, 0 = off-topic or empty.
accuracy (0-2): does the answer state anything from WRONG FACTS?
  2 = none of them, 0 = states at least one.

QUESTION: {question}
GOLD FACTS: {gold_facts}
WRONG FACTS: {distractors}
ANSWER: {answer}

Reply with exactly this JSON shape:
{{"groundedness": 0, "relevance": 0, "accuracy": 0}}
"""


class LLMJudge:
    """Minimal OpenAI-compatible chat-completions judge.

    Works with any endpoint that speaks the OpenAI chat-completions shape
    (OpenAI, or a Gemini OpenAI-compatibility endpoint). Uses only the
    standard library so the repo needs no LLM SDK dependency.
    """

    def __init__(self, api_key: str | None = None,
                 base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") \
            or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "LLM judge needs an API key: set OPENAI_API_KEY or "
                "GEMINI_API_KEY. The deterministic judge (default) needs none.")
        self.base_url = base_url.rstrip("/")
        self.model = model

    def score_case(self, case: dict, answer: str) -> dict:
        prompt = RUBRIC_PROMPT.format(
            question=case["question"],
            gold_facts=", ".join(case.get("gold_facts", [])) or "(none)",
            distractors=", ".join(case.get("distractors", [])) or "(none)",
            answer=answer,
        )
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }).encode()
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read())
        content = body["choices"][0]["message"]["content"]
        scores = json.loads(content)
        total = int(scores["groundedness"]) + int(scores["relevance"]) \
            + int(scores["accuracy"])
        return {
            "id": case["id"],
            "question": case["question"],
            "answer": answer,
            "groundedness": int(scores["groundedness"]),
            "relevance": int(scores["relevance"]),
            "accuracy": int(scores["accuracy"]),
            "total": total,
            "passed": total >= 4 and int(scores["accuracy"]) == 2,
            "critical": int(scores["accuracy"]) == 0,
            "matched_distractors": [],
            "judge": f"llm:{self.model}",
        }

"""Opt-in OpenAI-compatible rubric judge; offline tests mock the HTTP boundary.

No live provider result is claimed. The deterministic judge remains the default.
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
                 base_url: str | None = None,
                 model: str | None = None) -> None:
        use_gemini = not (api_key or os.environ.get("OPENAI_API_KEY"))
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") \
            or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "LLM judge needs an API key: set OPENAI_API_KEY or "
                "GEMINI_API_KEY. The deterministic judge (default) needs none.")
        default_url = ("https://generativelanguage.googleapis.com/v1beta/openai"
                       if use_gemini else "https://api.openai.com/v1")
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL")
                         or default_url).rstrip("/")
        self.model = (model or os.environ.get("LLM_MODEL")
                      or ("gemini-2.5-flash" if use_gemini else "gpt-4o-mini"))

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
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read())
            scores = json.loads(body["choices"][0]["message"]["content"])
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            # Do not echo provider error bodies, credentials or raw model output.
            raise RuntimeError("LLM judge request failed or returned malformed JSON") from None
        if (not isinstance(scores, dict)
                or set(scores) != {"groundedness", "relevance", "accuracy"}
                or any(type(scores[k]) is not int or scores[k] not in allowed
                       for k, allowed in (("groundedness", (0, 1, 2)),
                                          ("relevance", (0, 1, 2)),
                                          ("accuracy", (0, 2))))):
            raise RuntimeError("LLM judge returned invalid rubric scores")
        total = sum(scores.values())
        return {
            "id": case["id"],
            "question": case["question"],
            "answer": answer,
            "groundedness": scores["groundedness"],
            "relevance": scores["relevance"],
            "accuracy": scores["accuracy"],
            "total": total,
            "passed": total >= 4 and scores["accuracy"] == 2,
            "critical": scores["accuracy"] == 0,
            "matched_distractors": [],
            "judge": f"llm:{self.model}",
        }

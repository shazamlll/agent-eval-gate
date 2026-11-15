import io
import json
from unittest.mock import patch

import pytest

from eval_gate.llm_judge import LLMJudge
from eval_gate.runner import main

CASE = {"id": "synthetic-1", "question": "What costs $12?",
        "gold_facts": ["$12"], "distractors": ["$99"]}


def response(scores):
    return io.BytesIO(json.dumps({"choices": [{"message": {
        "content": json.dumps(scores)}}]}).encode())


def test_gemini_key_selects_gemini_endpoint():
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-only"}, clear=True):
        judge = LLMJudge()
    assert judge.base_url == "https://generativelanguage.googleapis.com/v1beta/openai"
    assert judge.model == "gemini-2.5-flash"


def test_request_and_valid_rubric():
    with patch("urllib.request.urlopen", return_value=response(
            {"groundedness": 2, "relevance": 1, "accuracy": 2})) as send:
        result = LLMJudge(api_key="test-only").score_case(CASE, "It costs $12")
    request = send.call_args.args[0]
    assert request.full_url == "https://api.openai.com/v1/chat/completions"
    assert json.loads(request.data)["response_format"] == {"type": "json_object"}
    assert result["passed"] is True
    assert result["total"] == 5


@pytest.mark.parametrize("scores", [
    {"groundedness": 99, "relevance": 2, "accuracy": 2},
    {"groundedness": True, "relevance": 2, "accuracy": 2},
    {"groundedness": "2", "relevance": 2, "accuracy": 2},
    {"groundedness": 1.5, "relevance": 2, "accuracy": 2},
    {"groundedness": -1, "relevance": 2, "accuracy": 2},
    {"groundedness": 2, "relevance": 2, "accuracy": 1},
    {"groundedness": 2},
    [],
])
def test_invalid_scores_fail_closed(scores):
    with patch("urllib.request.urlopen", return_value=response(scores)):
        with pytest.raises(RuntimeError, match="invalid rubric"):
            LLMJudge(api_key="test-only").score_case(CASE, "answer")


def test_malformed_response_is_cli_error_without_secret(capsys, tmp_path):
    with patch.dict("os.environ", {"OPENAI_API_KEY": "secret-test-only"}, clear=True), \
         patch("urllib.request.urlopen", return_value=io.BytesIO(b"not-json")):
        assert main(["--judge", "llm", "--output-dir", str(tmp_path)]) == 2
    assert "secret-test-only" not in capsys.readouterr().err
    assert not (tmp_path / "results.json").exists()


def test_wrong_fact_is_critical():
    with patch("urllib.request.urlopen", return_value=response(
            {"groundedness": 2, "relevance": 2, "accuracy": 0})):
        result = LLMJudge(api_key="test-only").score_case(CASE, "$99")
    assert result["critical"] is True
    assert result["passed"] is False

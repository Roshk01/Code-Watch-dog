import os
import sys
import json
from unittest.mock import patch, MagicMock
import pytest  # type: ignore[import-not-found]
from pydantic import ValidationError

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.agent_review import use_llama_70b_versatile, use_gpt_oss_120b, review_code


def valid_llm_response_json():
    return json.dumps({
        "code_quality": {"score": 8, "overall_feedback": "Clean code."},
        "security_issues": [],
        "suggestions": ["Add type hints"],
        "summary": "Looks good.",
    })


def make_mock_response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=content))]
    return mock_response


@patch("app.agent_review.client.chat.completions.create")
def test_groq_call_retries_then_succeeds(mock_create):
    mock_create.side_effect = [
        Exception("timeout"),
        Exception("timeout"),
        make_mock_response(valid_llm_response_json()),
    ]
    result = use_llama_70b_versatile("some code diff")
    assert result["code_quality"]["score"] == 8
    assert mock_create.call_count == 3


@patch("app.agent_review.client.chat.completions.create")
def test_groq_call_fails_after_max_attempts(mock_create):
    mock_create.side_effect = Exception("still broken")
    with pytest.raises(Exception):
        use_llama_70b_versatile("some code diff")
    assert mock_create.call_count == 3


@patch("app.agent_review.use_gpt_oss_120b")
@patch("app.agent_review.use_llama_70b_versatile")
def test_review_code_falls_back_on_llama_failure(mock_llama, mock_gpt):
    mock_llama.side_effect = Exception("llama broke")
    mock_gpt.return_value = {
        "code_quality": {"score": 6, "overall_feedback": "ok"},
        "security_issues": [],
        "suggestions": [],
        "summary": "fallback worked",
        "too_large": False,
    }
    result = review_code("some code diff", complexity="medium")
    assert result["summary"] == "fallback worked"
    mock_gpt.assert_called_once()


@patch("app.agent_review.use_gpt_oss_120b")
@patch("app.agent_review.use_llama_70b_versatile")
def test_review_code_falls_back_on_validation_error_not_retry_same_model(mock_llama, mock_gpt):
    mock_llama.side_effect = ValidationError.from_exception_data("ReviewResult", [])
    mock_gpt.return_value = {
        "code_quality": {"score": 5, "overall_feedback": "ok"},
        "security_issues": [],
        "suggestions": [],
        "summary": "fallback after bad schema",
        "too_large": False,
    }
    result = review_code("some code diff", complexity="medium")
    assert result["summary"] == "fallback after bad schema"
    mock_llama.assert_called_once()  # not retried internally for validation errors
    mock_gpt.assert_called_once()
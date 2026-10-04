import sys
import os
import unittest
from pydantic import ValidationError

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.agent_review import ReviewResult


def valid_review_dict():
    return {
        "code_quality": {"score": 7, "overall_feedback": "Looks good overall."},
        "security_issues": [{"line": 12, "description": "Hardcoded API key."}],
        "suggestions": ["Add docstrings", "Handle edge case for empty input"],
        "summary": "Minor issues, otherwise solid.",
    }


def test_valid_data_passes():
    data = valid_review_dict()
    result = ReviewResult(**data)  # should NOT raise
    assert result.code_quality.score == 7
    assert result.too_large is False  # default value


def test_missing_required_field_fails():
    data = valid_review_dict()
    del data["summary"]  # remove a required field
    with unittest.TestCase().assertRaises(ValidationError):
        ReviewResult(**data)


def test_wrong_type_for_score_fails():
    data = valid_review_dict()
    data["code_quality"]["score"] = "seven"  # should be int, not str
    with unittest.TestCase().assertRaises(ValidationError):
        ReviewResult(**data)


def test_security_issue_missing_line_fails():
    data = valid_review_dict()
    data["security_issues"] = [{"description": "Missing the 'line' field"}]
    with unittest.TestCase().assertRaises(ValidationError):
        ReviewResult(**data)


def test_suggestions_wrong_type_fails():
    data = valid_review_dict()
    data["suggestions"] = "should be a list, not a string"
    with unittest.TestCase().assertRaises(ValidationError):
        ReviewResult(**data)
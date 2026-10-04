import os
import sys
import hmac
import hashlib
import json
from unittest.mock import patch, MagicMock
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app, github_webhook_secret


client = TestClient(app)


def make_signature(secret: str | None, body: bytes) -> str:
    assert secret is not None
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def sample_payload():
    return {
        "action": "opened",
        "pull_request": {"number": 1, "diff_url": "https://fake.url/diff"},
        "repository": {"full_name": "someuser/somerepo"},
    }


@patch("app.main.requests.get")
def test_diff_fetch_retries_then_succeeds(mock_get):
    # First 2 calls fail, 3rd succeeds
    fail_response = MagicMock()
    fail_response.raise_for_status.side_effect = requests.exceptions.RequestException("boom")

    success_response = MagicMock()
    success_response.raise_for_status.return_value = None
    success_response.text = "diff --git a/file.py b/file.py\n+print('hi')"

    mock_get.side_effect = [fail_response, fail_response, success_response]

    body = json.dumps(sample_payload()).encode()
    sig = make_signature(github_webhook_secret, body)

    with patch("app.main.classify_complexity", return_value="low"), \
         patch("app.main.review_code", return_value={"summary": "ok", "too_large": False}), \
         patch("app.main.post_review") as mock_post:

        response = client.post(
            "/webhook",
            content=body,
            headers={
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "pull_request",
                "Content-Type": "application/json",
            },
        )

    assert response.status_code == 200
    assert mock_get.call_count == 3  # confirms it actually retried twice before succeeding
    mock_post.assert_called_once()


@patch("app.main.requests.get")
def test_diff_fetch_fails_after_max_attempts(mock_get):
    fail_response = MagicMock()
    fail_response.raise_for_status.side_effect = requests.exceptions.RequestException("Still broken")
    mock_get.return_value = fail_response

    body = json.dumps(sample_payload()).encode()
    sig = make_signature(github_webhook_secret, body)

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 502
    assert mock_get.call_count == 3  # all 3 attempts were used before giving up
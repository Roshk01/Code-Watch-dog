import os
import sys
import hmac
import hashlib

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.main import verify_signature, github_webhook_secret

def make_signature(secret, payload):
    """Helper function to create a valid HMAC signature for testing."""
    digest = hmac.new(secret.encode("UTF-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"

def test_valid_signature():
    payload = b'{"action": "opened"}'
    signature = make_signature(github_webhook_secret, payload)
    assert verify_signature(payload, signature) == True

def test_tampered_signature_fails():
    body = b'{"action": "opened"}'
    sig = make_signature(github_webhook_secret, body)
    # flip the last character so it's wrong but same length/format
    tampered = sig[:-1] + ("0" if sig[-1] != "0" else "1")
    assert verify_signature(body, tampered) is False


def test_wrong_body_fails():
    body = b'{"action": "opened"}'
    sig = make_signature(github_webhook_secret, body)
    different_body = b'{"action": "closed"}'
    assert verify_signature(different_body, sig) is False


def test_missing_prefix_fails():
    body = b'{"action": "opened"}'
    assert github_webhook_secret is not None
    digest = hmac.new(github_webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, digest) is False  # no "sha256=" prefix


def test_missing_header_fails():
    body = b'{"action": "opened"}'
    assert verify_signature(body, None) is False
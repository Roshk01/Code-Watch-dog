from fastapi import FastAPI, Request, Header, HTTPException
from dotenv import load_dotenv
from app.agent_review import review_code, classify_complexity
from app.github_utils import post_review
import os
import requests
import hmac
import hashlib

load_dotenv()
github_token = os.getenv("GitHub_token")
github_webhook_secret = os.getenv("WEBHOOK_SECRET")

if not github_webhook_secret:
    raise ValueError("WEBHOOK_SECRET not found in .env file!")

app = FastAPI()


@app.get("/")
def health():
    return {"status": "codewatchdog is running"}


@app.get("/test-review")
def test_review():
    sample_diff = "+++ b/app.py\n+def add(a, b):\n+    return a + b();;\n+password = 'admin123'\n"
    complexity = classify_complexity(sample_diff)
    return {"complexity": complexity, "review": review_code(sample_diff, complexity=complexity)}


# webhook signature verification function
def verify_signature(payload_body: bytes, signature_header:str | None)-> bool:

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_signature = hmac.new(
        key=github_webhook_secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    received_signature = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected_signature, received_signature)

# handle only PR open Events
@app.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None)
):
    raw_body = await request.body()
    if not verify_signature(raw_body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event != "pull_request":
        return {'status': 'Ignored'}
    
    data = await request.json()

    # only handle PR open events
    action = data.get('action')
    if action != 'opened':
        return {'status': 'Ignored'}
    pr_no = data['pull_request']['number']
    repo_name = data['repository']['full_name']
    pr_diff_url = data['pull_request']['diff_url']

    print(f"Received PR #{pr_no} in repo {repo_name}. \n Diff URL: {pr_diff_url}")

    # step 1 fetch the diff
    headers = {'authorization': f'token {github_token}'}
    diff_response = requests.get(pr_diff_url, headers=headers)
    diff_content = diff_response.text

    # step 2 classify complexity and call the code review agent
    complexity = classify_complexity(diff_content)
    print(f'Complexity of PR #{pr_no}: {complexity}')
    review = review_code(diff_content, complexity=complexity)
    print(f'Review for PR #{pr_no}:\n{review}')

    # step 3 post the review back to Github
    post_review(repo_name, pr_no, review)


    return {'status': 'PR Reviewed & comment posted', 'pr_no': pr_no, 'repo_name': repo_name}
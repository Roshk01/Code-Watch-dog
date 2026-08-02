from fastapi import FastAPI, Request, Header
from dotenv import load_dotenv
from agent_review import review_code, classify_complexity
from github_utils import post_review
import os
import requests

load_dotenv()
github_token = os.getenv("GitHub_token")

app = FastAPI()

# handle only PR open Events
@app.post("/webhook")
async def github_webhook(request: Request):
    
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
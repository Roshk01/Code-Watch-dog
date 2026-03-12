import os
from github import Github
from dotenv import load_dotenv
import re
import json

load_dotenv()  # Load environment variables from .env file
github_token = os.getenv("GitHub_token")
if not github_token:
    raise ValueError("GITHUB_TOKEN not found in .env file!")

def post_review(repo_name: str, pr_number: int, review: str):
    try:
        # connect to GitHub using the token
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Extract JSON object from the response
        json_match = re.search(r'\{.*\}', review, re.DOTALL)
        if not json_match:
            print("No JSON found in review response!")
            return
        
        clean_review = json_match.group()

        # parse the json review content
        review = json.loads(clean_review)

        # create a clean comment body for the review
        score = review['code_quality']['score']
        feedback = review['code_quality']['overall_feedback']
        summary = review['summary']
        suggestion = review['suggestions']
        security = review['security_issues']


        comment_body = f""" 
## code watch Dog Review 🐕
## Code Quality Score: {score}/10
{feedback}
        
## security issues:
"""
        if security:
            for issue in security:
                comment_body += f'** Line {issue["line"]}** {issue["description"]} \n'
        else:
            comment_body += "No security issues found. \n"
        
        comment_body += "## Suggestions: \n"
        for s in suggestion:
            comment_body += f'- {s} \n'
        comment_body += f"## Summary: \n {summary}"

        pr.create_issue_comment(comment_body)
        print(f"Posted review comment on PR successfully #{pr_number} in repo {repo_name}")


    except json.JSONDecodeError:
        print("Failed to decode JSON response from LLM. Review content:")
    except Exception as e:
        print(f"An error occurred while posting the review: {e}")
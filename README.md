# CodeWatchdog

A GitHub bot that reviews pull requests automatically. When a PR is opened, it reads the diff, asks an LLM (via Groq) to look for bugs and security problems, and posts the result as a comment on the PR.

---

## How It Works

```
Pull Request opened
        |
        v
GitHub webhook  --POST /webhook-->  FastAPI server
                                        |
                                        v
                          Verify HMAC signature (X-Hub-Signature-256)
                          Check event type (pull_request, action: opened)
                                        |
                                        v
                                Fetch diff via GitHub API
                                        |
                                        v
                          Classify diff size: simple / moderate / complex
                                        |
                                        v
                        Review with Groq (model depends on size)
                        primary model fails -> backup model
                                        |
                                        v
                              Parse JSON review output
                                        |
                                        v
                             Post comment on the PR
```

---

## Features

- Reviews every newly opened pull request
- Returns a code quality score (out of 10), security findings, suggestions, and a summary
- Rejects webhook requests that lack a valid GitHub signature
- Routes small diffs to a smaller, cheaper model to save tokens
- Falls back to a second Groq model if the primary call fails
- Returns a clear "review unavailable" comment if both models fail, instead of crashing

---

## Model Routing

| Diff size (changed lines) | Model |
|---|---|
| 20 or fewer (simple) | `llama-3.1-8b-instant` |
| 21 and above (moderate / complex) | `llama-3.3-70b-versatile` |
| Any tier, if the model call fails | `openai/gpt-oss-120b` (backup) |

The thresholds are a starting point and haven't been tuned against real PR sizes yet.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Server | FastAPI + Uvicorn |
| LLM | Groq API (Llama 3.1 8B, Llama 3.3 70B, GPT-OSS 120B) |
| GitHub integration | Webhooks + PyGithub |
| Language | Python 3.11 |
| Hosting | Runs locally, exposed with VS Code port forwarding |

---

## Project Structure

```
Code-Watch-dog/
├── main.py                # FastAPI app: webhook route, signature check, orchestration
├── app/
│   ├── __init__.py
│   ├── agent_review.py    # Complexity classifier, Groq calls, model fallback
│   └── github_utils.py    # Parses the review and posts the PR comment
├── .env                   # Secrets (never commit this)
├── .gitignore
└── requirements.txt
```

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/Roshk01/Code-Watch-dog.git
cd Code-Watch-dog
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Create a `.env` file in the project root**
```
GitHub_token=your_fine_grained_github_token
llm_api_key=your_groq_api_key
WEBHOOK_SECRET=a_long_random_string
```
Generate the webhook secret with `python -c "import secrets; print(secrets.token_hex(32))"`. Variable names are case-sensitive on Linux, so keep them exactly as written.

**4. Run the server** (from the project root, where `.env` lives)
```bash
uvicorn main:app --port 8000
```

**5. Expose the server and register the webhook**

Forward port 8000 with VS Code (set the port's visibility to **Public**) or another tunnel, then add a webhook:
- Repo → Settings → Webhooks → Add webhook
- Payload URL: `https://your-forwarded-url/webhook`
- Content type: `application/json`
- Secret: the same value as `WEBHOOK_SECRET` in `.env`
- SSL verification: enabled
- Events: select individual events, then **Pull requests** only

Restart uvicorn after any change to `.env`, since it is only read at startup.

---

## GitHub Token Permissions

Create a fine-grained personal access token limited to the repository the bot reviews:

| Permission | Level |
|---|---|
| Pull requests | Read and write |
| Contents | Read only |
| Metadata | Read only |

---

## Review Output Example

```
Code Watch Dog Review

Code Quality Score: 4/10
The code has several security vulnerabilities and lacks best practices.

Security Issues:
- Line 6: SQL injection vulnerability due to string concatenation
- Line 14: Hardcoded API key found in plain text

Suggestions:
- Use parameterized queries to prevent SQL injection
- Store credentials in environment variables

Summary:
The code requires significant improvements to ensure security and reliability.
```

---

## Known Limitations

- The model only sees the diff, not the whole repository, so it can flag things that are fine in context.
- Line numbers in findings refer to positions in the diff, not line numbers in the file.
- Only the `opened` action is handled. Pushing new commits to an existing PR does not trigger a new review.
- Review quality depends on the prompt and model, and findings can be generic.
- There is no automated test suite yet.

## Planned Work

- Validate the model's JSON output with Pydantic and retry on malformed responses
- Add diff size limits and request timeouts
- Tighten the review prompt so findings stay tied to the changed lines
- Add tests and CI

---

## License

MIT License

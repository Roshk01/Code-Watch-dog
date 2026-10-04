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
                        Fetch diff via GitHub API (3 retries, timeout)
                                        |
                                        v
                          Classify diff size: low / medium / high / too_large
                                        |
                                        v
                    too_large? --> skip LLM, post "manual review required"
                                        |
                                        v
                 Review with Groq (model depends on size, 3 retries, timeout)
                 untrusted diff wrapped in <diff> tags, separated from
                 trusted system prompt (prompt-injection mitigation)
                 primary model fails or returns invalid JSON -> backup model
                                        |
                                        v
                    Validate output against Pydantic schema
                                        |
                                        v
                             Post comment on the PR
```

---

## Features

- Reviews every newly opened pull request
- Returns a code quality score (out of 10), security findings, suggestions, and a summary
- Rejects webhook requests that lack a valid, HMAC-verified GitHub signature
- Separates trusted instructions from untrusted diff content to reduce prompt-injection risk
- Routes diffs to a model based on size, to balance cost and review depth
- Rejects diffs over 300 changed lines outright and posts a "manual review required" comment, instead of reviewing a diff too large to review well
- Validates the model's JSON output against a schema before posting, instead of trusting it blindly
- Retries transient failures (timeouts, network errors) on both the GitHub diff fetch and the Groq call, before giving up
- Falls back to a second Groq model if the primary call fails or returns a response that doesn't match the expected schema
- Returns a clear "review unavailable" comment if both models fail, instead of crashing

---

## Model Routing

| Diff size (changed lines) | Complexity | Model |
|---|---|---|
| 0–20 | low | `openai/gpt-oss-20b` |
| 21–149 | medium | `openai/gpt-oss-120b` |
| 150–299 | high | `openai/gpt-oss-120b` |
| 300+ | too_large | Not reviewed — PR comment requests manual review |

Both models are free-tier on Groq. If the primary model call fails, times out, or returns output that fails schema validation, the bot retries that model up to 3 times, then falls back to the other GPT-OSS model (20b ↔ 120b).

The thresholds are a starting point and haven't been tuned against real PR sizes yet.

> **Note:** Llama 3.1 8B and Llama 3.3 70B, previously used here, moved to Groq's Enterprise tier and are no longer available on the free tier — replaced with the GPT-OSS models above.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Server | FastAPI + Uvicorn |
| LLM | Groq API (GPT-OSS 20B, GPT-OSS 120B) |
| GitHub integration | Webhooks + PyGithub |
| Language | Python 3.11 |
| Hosting | Runs locally, exposed with VS Code port forwarding |

---

## Project Structure

```
Code-Watch-dog/
├── main.py                       # FastAPI app: webhook route, signature check, orchestration
├── app/
│   ├── __init__.py
│   ├── agent_review.py           # Complexity classifier, Groq calls + retries, Pydantic validation, model fallback
│   └── github_utils.py           # Parses the review and posts the PR comment
├── tests/
│   ├── test_webhook_signature.py # Unit tests for HMAC signature verification
│   ├── test_review_schema.py     # Unit tests for the Pydantic review schema
│   └── test_groq_review.py       # Mocked tests for Groq retries and model fallback
├── .github/
│   └── workflows/
│       └── tests.yml             # CI: runs the test suite on every push/PR
├── .env                          # Secrets (never commit this)
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

## Testing & CI

Run the full test suite locally:
```bash
pytest -v
```
Pytest auto-discovers every `test_*.py` file under `tests/` — no need to run files individually. External calls (GitHub API, Groq API) are mocked, so tests run without real network access or credentials.

A GitHub Actions workflow (`.github/workflows/tests.yml`) runs this same suite automatically on every push and pull request against `main`.

---

## Known Limitations

- The model only sees the diff, not the whole repository, so it can flag things that are fine in context.
- Line numbers in findings refer to positions in the diff, not line numbers in the file.
- Only the `opened` action is handled. Pushing new commits to an existing PR does not trigger a new review.
- Review quality depends on the prompt and model, and findings can be generic.
- Diffs over 300 changed lines are skipped entirely (flagged for manual review) rather than partially reviewed.
- No retrieval of past reviews or a persistent review history yet — each PR is reviewed independently, with nothing stored for later analysis.

## Planned Work

- Tighten the review prompt so findings stay tied to the changed lines
- Review on `synchronize` (new commits pushed to an existing PR), not just `opened`
- Split oversized diffs by file instead of rejecting them outright, so partial reviews are possible
- A metrics dashboard (e.g. Streamlit) showing review history and score trends over time — would need a persistence layer (e.g. SQLite) first, since nothing is currently stored

---

## License

MIT License

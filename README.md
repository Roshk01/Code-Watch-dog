# CodeWatchdog

An AI-powered GitHub bot that automatically reviews pull requests and posts feedback directly on your PR — detecting bugs, security vulnerabilities, and bad code patterns using Llama 3.3 70B via Groq.

---

## How It Works

```
Pull Request Opened
        |
        v
GitHub Webhook  ──────────────────>  FastAPI Server
                                            |
                                            v
                                    Fetch Code Diff
                                    (GitHub API)
                                            |
                                            v
                                    Send to Llama 3.3 70B
                                    (Groq API)
                                            |
                                            v
                                    Parse Review (JSON)
                                            |
                                            v
                                Post Comment on GitHub PR
```

---

## Features

- Automatic PR review on every pull request opened
- Detects SQL injection, hardcoded secrets, and common vulnerabilities
- Gives a code quality score out of 10
- Posts structured review comments directly on GitHub
- Works with any repository via webhook setup

---

## Tech Stack

| Layer | Technology |
|---|---|
| Server | FastAPI |
| AI Model | Llama 3.3 70B (via Groq) |
| GitHub Integration | PyGithub + Webhooks |
| Language | Python 3.10+ |
| Deployment | Render |

---

## Project Structure

```
CodeWatchdog/
├── app/
│   ├── main.py            # FastAPI server and webhook handler
│   ├── groq_review.py     # Groq API and code review logic
│   └── github_utils.py    # GitHub API - fetch diff and post comments
├── .env                   # API keys (never commit this)
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

**3. Add your API keys in `.env`**
```
GITHUB_TOKEN=your_github_token
GROQ_API_KEY=your_groq_api_key
```

**4. Run the server**
```bash
uvicorn app.main:app --reload
```

**5. Expose your server publicly**

Use VS Code port forwarding or ngrok, then add the URL as a GitHub webhook:
- Go to your repo → Settings → Webhooks → Add webhook
- Payload URL: `https://your-url/webhook`
- Content type: `application/json`
- Events: Pull requests only

---

## GitHub Token Permissions

When creating a Fine-Grained token, set:

| Permission | Level |
|---|---|
| Pull Requests | Read and Write |
| Contents | Read only |
| Metadata | Read only |

---

## Review Output Example

When a PR is opened, CodeWatchdog posts a comment like:

```
Code Watch Dog Review

Code Quality Score: 4/10
The code has several security vulnerabilities and lacks best practices.

Security Issues:
- Line 6: SQL injection vulnerability due to string concatenation
- Line 14: Hardcoded API key found in plain text
- Line 15: Hardcoded database password

Suggestions:
- Use parameterized queries to prevent SQL injection
- Store sensitive credentials in environment variables
- Add proper error handling and input validation

Summary:
The code requires significant improvements to ensure security and reliability.
```

---

## API Keys

| Service | Where to get it | Cost |
|---|---|---|
| Groq API | console.groq.com | Free tier available |
| GitHub Token | GitHub Settings → Developer Settings | Free |

---

## License

MIT License
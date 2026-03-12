# Code-Watch-dog
An AI-powered GitHub bot that automatically reviews pull requests, detects bugs, security issues, and bad patterns using "llama-3.3-70b-versatile" model


# check version 4
## Test Section

This is a test change to trigger CodeWatchdog review.

### Sample Bad Code
```python
import sqlite3

def login(username, password):
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    conn = sqlite3.connect("users.db")
    result = conn.execute(query)
    return result

API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"
```

### Notes
- Added test section
- Testing CodeWatchdog bot

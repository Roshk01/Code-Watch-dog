import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # Load environment variables from .env file
llm_key = os.getenv("llm_api_key")

# The client automatically picks up the GROQ_API_KEY environment variable
client = Groq(api_key=llm_key)


# prompt for my code review assistant
def PR_Agent(code):
    prompt = f"""
    You are an expert code reviewer on GitHub. Analyze the provided code and evaluate it for quality, structure, readability, maintainability, and security vulnerabilities.

    Return ONLY a valid JSON object. No extra text, no markdown, no code blocks.

    {{
        "code_quality": {{
            "score": 7,
            "overall_feedback": "single string summary here"
        }},
        "security_issues": [
            {{
                "line": 2,
                "description": "describe issue and how to fix it"
            }}
        ],
        "suggestions": [
            "suggestion 1",
            "suggestion 2",
            "suggestion 3"
        ],
        "summary": "concise overall summary here"
    }}

    """
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": code}
        ],
        model="llama-3.3-70b-versatile"  # Example model, check Groq docs for latest models
    )

    return response.choices[0].message.content

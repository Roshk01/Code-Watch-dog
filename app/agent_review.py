import os
from dotenv import load_dotenv
import requests
import json
from groq import Groq

load_dotenv()  # Load environment variables from .env file
llm_key = os.getenv("llm_api_key")

# The client automatically picks up the GROQ_API_KEY environment variable
client = Groq(api_key=llm_key)


# prompt for my code review assistant
prompt = """
You are an expert code reviewer on GitHub. Analyze the provided code and evaluate it for quality, structure, readability, maintainability, and security vulnerabilities.

Return ONLY a valid JSON object. No extra text, no markdown, no code blocks.

{
    "code_quality": {
        "score": 7,
        "overall_feedback": "single string summary here"
    },
    "security_issues": [
        {
            "line": 2,
            "description": "describe issue and how to fix it"
        }
    ],
    "suggestions": [
        "suggestion 1",
        "suggestion 2",
        "suggestion 3"
    ],
    "summary": "concise overall summary here"
}

""" 
def use_llama_70b_versatile(code: str) -> str:
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": code}
        ],
        model="llama-3.3-70b-versatile"  # Example model, check Groq docs for latest models
    )

    return response.choices[0].message.content

def use_gpt_oss_120b(code: str) -> str:
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": code}
        ],
        model="openai/gpt-oss-120b"  # Example model, check Groq docs for latest models
    )

    return response.choices[0].message.content


def review_code(code: str, complexity: str) -> dict:
    if complexity == "low":
        print("Using openai API for low complexity code...")
        return use_gpt_oss_120b(code)
    else:
        try:
            print("Trying llama-3.3-70b-versatile Model...")
            result = use_llama_70b_versatile(code)
            print("llama-3.3-70b-versatile succeeded!")
            return result
        except Exception as e:
            print("llama-3.3-70b-versatile Fail")
            print("trying Fallback model -> openapi [openai/gpt-oss-120b]...")
            try:
                result= use_gpt_oss_120b(code)
                print("OpenAI API succeeded!")
                return result
            except Exception as e:
                print("OpenAI API also failed.")
                # return a default response indicating both services are unavailable
                return json.dumps({
                    "code_quality": {"score": 0, "overall_feedback": "Review service unavailable"},
                    "security_issues": [],
                    "suggestions": ["Please try again later"],
                    "summary": "Both llama and OpenAI review services are currently unavailable"
                })
            
def classify_complexity(diff_content: str) -> str:
    """
    classify the complexity of the code diff based on the number of lines 
    changed and the types of changes made.
    """
    lines_changed = len(diff_content.splitlines())
    if lines_changed <= 20:
        return "low"
    elif lines_changed>=21 and lines_changed < 150:
        return "medium"
    else:
        return "high"

if __name__ == "__main__":
    # Example usage
    example_code = """def add(a, b):
    return a + b();; """
    complexity = classify_complexity(example_code)
    review_result = review_code(example_code, complexity=complexity)
    print("Review Result:", review_result)
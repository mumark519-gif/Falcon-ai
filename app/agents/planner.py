import json
import google.generativeai as genai
from app.core.config import settings

PLANNER_PROMPT = """
You are Falcon AI Planner.

Your job is NOT to answer the user's question.

Your job is to produce an execution plan in VALID JSON.

Return ONLY JSON.

Format:

{
  "steps": [
    {
      "type": "agent",
      "agent": "BUSINESS",
      "task": "..."
    }
  ]
}

Available agents:

BUSINESS
CODING
INVESTMENT
RESEARCH

Available tools:

Available tools:

web_search
document_search
python

A step can be either:

{
  "type": "tool",
  "tool": "web_search",
  "input": "latest NVIDIA earnings"
}

or

{
  "type": "agent",
  "agent": "RESEARCH",
  "task": "Analyze the latest NVIDIA earnings"
}

Examples:

User:
Should I invest in Apple stock?

Output:

{
  "steps": [
    {
      "type": "agent",
      "agent": "RESEARCH",
      "task": "Research Apple's financial position"
    },
    {
      "type": "agent",
      "agent": "INVESTMENT",
      "task": "Evaluate Apple as an investment"
    }
  ]
}

User:
Fix my FastAPI authentication error.

Output:

{
  "steps": [
    {
      "type": "agent",
      "agent": "CODING",
      "task": "Analyze the FastAPI authentication error"
    }
  ]
}

User:
Calculate the factorial of 20 using Python.

Output:

{
  "steps": [
    {
      "type": "tool",
      "tool": "python",
      "input": "print(__import__('math').factorial(20))"
    }
  ]
}

User:
Research NVIDIA's latest earnings and tell me whether it is a good investment.

Output:

{
  "steps": [
    {
      "type": "tool",
      "tool": "web_search",
      "input": "NVIDIA latest earnings"
    },
    {
      "type": "agent",
      "agent": "RESEARCH",
      "task": "Summarize NVIDIA's latest earnings"
    },
    {
      "type": "agent",
      "agent": "INVESTMENT",
      "task": "Evaluate NVIDIA as an investment using the research findings"
    }
  ]
}

Always return valid JSON.

Never explain.

Never use markdown.

Never answer the user.
"""




genai.configure(
    api_key=settings.GOOGLE_API_KEY
)

def create_plan(question: str):

    model = genai.GenerativeModel(
        "gemini-2.5-flash"
    )

    response = model.generate_content(
        PLANNER_PROMPT
        + "\n\nUser Request:\n"
        + question
    )

    try:
        return json.loads(response.text)
    except Exception:
        return {
            "steps": [
                {
                    "type": "agent",
                    "agent": "RESEARCH",
                    "task": question
                }
            ]
        }
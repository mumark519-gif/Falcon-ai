import json

import google.generativeai as genai

from app.agents.router import get_system_prompt
from app.core.config import settings
from google.api_core.exceptions import ResourceExhausted

genai.configure(
    api_key=settings.GOOGLE_API_KEY
)


model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def analyze_business_problem(problem: str):
    problem = problem.lower()

    analysis = []

    if "sales" in problem:
        analysis.append(
            "📈 Sales: Review your sales process and identify where customers are dropping off."
        )

    if "marketing" in problem:
        analysis.append(
            "📢 Marketing: Improve digital marketing, SEO, and social media campaigns."
        )

    if "customer" in problem:
        analysis.append(
            "👥 Customer Service: Reduce response times and improve customer satisfaction."
        )

    if "finance" in problem or "money" in problem or "cost" in problem:
        analysis.append(
            "💰 Finance: Reduce unnecessary expenses and improve cash flow."
        )

    if "employee" in problem or "staff" in problem:
        analysis.append(
            "🏢 Human Resources: Invest in employee training and performance management."
        )

    if "competition" in problem or "competitor" in problem:
        analysis.append(
            "⚔️ Competition: Analyze competitors and create a stronger value proposition."
        )

    if not analysis:
        analysis.append(
            "🚀 Overall Recommendation: Gather more business data before making strategic decisions."
        )

    return {
        "business_problem": problem,

        "executive_summary": (
            "Falcon AI analyzed the business problem and generated "
            "strategic recommendations."
        ),

        "recommendations": analysis,

        "strengths": [
            "Business is actively seeking improvement",
            "Management is using AI for decision making",
        ],

        "weaknesses": [
            "Current issue requires attention",
            "Limited business information available",
        ],

        "opportunities": [
            "Increase efficiency",
            "Improve customer satisfaction",
            "Expand market reach",
        ],

        "risks": [
            "Revenue may continue declining",
            "Competitors may gain market share",
        ],

        "priority": "High",

        "action_plan": [
            "Week 1: Collect business performance data.",
            "Week 2: Implement Falcon AI recommendations.",
            "Week 3: Measure results and adjust strategy.",
            "Week 4: Review progress and plan next actions.",
        ],
    }


def ask_ai(prompt: str):

    system_prompt = get_system_prompt(prompt) + """
    
The conversation history below is your memory.

Always answer using the conversation history.

If the user asks:
- What did I say before?
- What was my previous message?
- What did you just tell me?

Answer from the conversation history.

Never say:
'I don't have memory.'

Never say:
'I cannot remember previous conversations.'

Only answer using the conversation history provided.
"""

    full_prompt = system_prompt + "\n\n" + prompt

    try:
        response = model.generate_content(full_prompt)

        return response.text

    except ResourceExhausted:

        return (
            "Falcon AI is temporarily unavailable because "
            "the AI service quota has been reached. "
            "Please try again later."
        )


def generate_chat_title(message: str):

    prompt = f"""
Generate a very short chat title (maximum 5 words).

Message:
{message}

Return ONLY the title.
"""

    try:

        response = model.generate_content(prompt)

        return response.text.strip()

    except ResourceExhausted:

        return "New Chat"

    except Exception:

        return "New Chat"


def extract_memory(message: str):

    prompt = f"""
Extract important personal facts from this message.

Return ONLY valid JSON.

Example:

{{
    "name": "Muhammad",
    "project": "Falcon AI"
}}

If there are no personal facts, return:

{{}}

Message:

{message}
"""

    try:

        response = model.generate_content(prompt)

        text = response.text.strip()

        text = (
            text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        return json.loads(text)

    except ResourceExhausted:

        return {}

    except Exception:

        return {}
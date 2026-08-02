from app.ai_service import ask_ai


def reason_about_plan(
    question: str,
    plan: dict,
):

    prompt = f"""
You are Falcon AI's Reasoning Engine.

User Question:

{question}

Execution Plan:

{plan}

Before executing the plan, think carefully.

Explain:

1. What is the user's real goal?
2. What information is missing?
3. Which tools are most useful?
4. Which agents are most useful?
5. What risks or mistakes should be avoided?

Return a concise reasoning summary.
"""

    return ask_ai(prompt)
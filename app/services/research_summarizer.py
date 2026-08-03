from app.ai_service import ask_ai

def summarize_research(
    pages,
):

    if not pages:

        return ""

    prompt = f"""
You are Falcon AI.

You have collected information from multiple webpages.

Your task:

- Remove duplicate information.
- Keep only important facts.
- Write one clear research summary.
- Do not mention repeated facts.
- Use simple, professional language.

Research:

{pages}
"""

    return ask_ai(
        prompt,
    )
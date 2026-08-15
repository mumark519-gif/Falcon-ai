from app.ai_service import ask_ai


def classify_memory_ai(memory: dict):

    prompt = f"""
You are Falcon AI's Memory Intelligence Engine.

Analyze the following memory:

{memory}

For each memory item determine:

1. Category
2. Importance (1-10)
3. Confidence (1-100)

Categories:

- personal
- preference
- project
- goal
- business
- skill
- work
- fact
- event
- other

Return ONLY valid JSON.
"""

    return ask_ai(prompt)
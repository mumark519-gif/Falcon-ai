from app.ai_service import ask_ai


def reflect(
    question: str,
    draft_answer: str,
):

    prompt = f"""
You are Falcon AI Reflection Engine.

User Question:

{question}

Draft Answer:

{draft_answer}

Review the draft carefully.

Check for:

1. Missing information
2. Incorrect reasoning
3. Hallucinations
4. Contradictions
5. Better explanations
6. Better structure
7. Better accuracy

If the answer is already excellent,
return it unchanged.

Otherwise improve it.

Return ONLY the final improved answer.
"""

    return ask_ai(prompt)
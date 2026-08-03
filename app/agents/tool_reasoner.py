from app.ai_service import ask_ai


def decide_tool_usage(
    question: str,
    plan: dict,
):

    prompt = f"""
You are Falcon AI's Tool Reasoner.

User Question:

{question}

Execution Plan:

{plan}

For each tool in the plan decide:

- USE
- SKIP

Rules:

- Don't use web search for general knowledge,
  math, coding, or reasoning.

- Use web search only if fresh or live
  information is needed.

- Use document search only if the
  user is asking about uploaded
  documents.

Return only a short explanation.
"""

    return ask_ai(prompt)
import json
from typing import Any


def build_prompt(
    plan: Any,
    memories: Any,
    messages: Any,
    knowledge: Any,
) -> str:
    """
    Build the final synthesis prompt for Falcon AI.

    The planner and document-search services may return structured objects
    rather than plain strings, so this function intentionally accepts
    flexible input types and serializes them safely for the model prompt.
    """

    prompt = "You are Falcon AI.\n\n"

    # ------------------------------------------------------------------
    # Execution plan
    # ------------------------------------------------------------------
    prompt += "Execution Plan:\n"

    try:
        prompt += json.dumps(
            plan,
            indent=2,
            default=str,
        )
    except (TypeError, ValueError):
        prompt += str(plan)

    prompt += "\n\n"

    # ------------------------------------------------------------------
    # User memories
    # ------------------------------------------------------------------
    if memories:
        prompt += "Known information about the user:\n"

        for memory in memories:
            key = getattr(memory, "key", "memory")
            value = getattr(memory, "value", memory)

            prompt += f"{key}: {value}\n"

        prompt += "\n"

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------
    prompt += "Conversation:\n"

    if messages:
        for msg in messages:
            role = getattr(msg, "role", "unknown")
            message = getattr(msg, "message", str(msg))

            prompt += f"{role}: {message}\n"

    # ------------------------------------------------------------------
    # Uploaded-document knowledge
    # ------------------------------------------------------------------
    if knowledge:
        prompt += (
            "\n\nRelevant knowledge "
            "from uploaded documents:\n"
        )

        if isinstance(knowledge, str):
            prompt += knowledge

        elif hasattr(knowledge, "text") and callable(knowledge.text):
            prompt += str(knowledge.text())

        else:
            try:
                prompt += json.dumps(
                    knowledge,
                    default=str,
                    indent=2,
                )
            except (TypeError, ValueError):
                prompt += str(knowledge)

    return prompt
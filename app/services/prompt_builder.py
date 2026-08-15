import json
def build_prompt(
    plan: str,
    memories,
    messages,
    knowledge: str,
):

    prompt = "You are Falcon AI.\n\n"

    prompt += "Execution Plan:\n"

    print(type(plan))
    print(plan)

    prompt += json.dumps(
        plan,
        indent=2
    )

    prompt += "\n\n"

    if memories:

        prompt += (
            "Known information about the user:\n"
        )

        for memory in memories:

            prompt += (
                f"{memory.key}: "
                f"{memory.value}\n"
            )

        prompt += "\n"

    prompt += "Conversation:\n"

    for msg in messages:

        prompt += (
            f"{msg.role}: "
            f"{msg.message}\n"
        )

    if knowledge:

        prompt += (
            "\n\nRelevant knowledge "
            "from uploaded documents:\n"
        )

        if isinstance(knowledge, str):
            prompt += knowledge
        elif hasattr(knowledge, "text") and callable(knowledge.text):
            prompt += knowledge.text()
        else:
            prompt += json.dumps(knowledge, default=str, indent=2)

    return prompt
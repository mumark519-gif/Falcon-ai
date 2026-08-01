def build_prompt(
    plan: str,
    memories,
    messages,
    knowledge: str,
):

    prompt = "You are Falcon AI.\n\n"

    prompt += "Execution Plan:\n"
    prompt += plan
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

        prompt += knowledge

    return prompt
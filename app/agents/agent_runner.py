from app.ai_service import ask_ai


def run_agent(
    system_prompt: str,
    question: str,
    context: dict | None = None,
    memories=None,
):

    if context is None:
        context = {}

    if memories is None:
        memories = []

    prompt = (
        system_prompt
        + "\n\nRelevant Memories:\n"
        + str(memories)
        + "\n\nShared Context:\n"
        + str(context)
        + "\n\nUser Question:\n"
        + question
    )

    return ask_ai(prompt)
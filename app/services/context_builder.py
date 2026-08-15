def build_context(
    memories=None,
    documents=None,
    research=None,
    tool_outputs=None,
    conversation=None,
):

    memories = memories or []
    documents = documents or []
    research = research or []
    tool_outputs = tool_outputs or []
    conversation = conversation or []

    context = {
        "memories": memories,
        "documents": documents,
        "research": research,
        "tools": tool_outputs,
        "conversation": conversation,
    }

    return context
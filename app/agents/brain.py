from app.agents.orchestrator import orchestrate


def think(
    db,
    username: str,
    question: str,
):
    """
    Canonical entry point for Falcon's cognitive system.

    Brain delegates the complete cognitive workflow
    to the central orchestrator.
    """

    result = orchestrate(
        db=db,
        username=username,
        question=question,
    )

    if result.get("error"):
        return result.get(
            "message",
            "Falcon encountered an internal error.",
        )

    return result.get(
        "answer",
        "",
    )
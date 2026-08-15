from app.models import Memory


def search_memories(
    db,
    username: str,
    query: str,
):

    memories = (
        db.query(Memory)
        .filter(
            Memory.username == username,
        )
        .all()
    )

    query_words = query.lower().split()

    ranked = []

    for memory in memories:

        score = 0

        text = (
            f"{memory.key} {memory.value}"
        ).lower()

        for word in query_words:

            if word in text:

                score += 1

        if score > 0:

            final_score = (
                score * 10
                + memory.importance
                + memory.access_count
            )

            ranked.append(
                (
                    final_score,
                    memory,
                )
            )

    ranked.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    return [
        memory
        for _, memory in ranked[:10]
    ]
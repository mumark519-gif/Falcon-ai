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

    return memories
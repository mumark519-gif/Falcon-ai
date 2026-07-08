from app.database import SessionLocal
from app.models import Memory


def get_memories(username):

    db = SessionLocal()

    memories = (
        db.query(Memory)
        .filter(Memory.username == username)
        .all()
    )

    db.close()

    return memories

def search_memories(username, message):

    db = SessionLocal()

    memories = (
        db.query(Memory)
        .filter(Memory.username == username)
        .all()
    )

    db.close()

    message = message.lower()

    relevant = []

    for memory in memories:

        if (
            memory.key.lower() in message
            or memory.value.lower() in message
        ):
            relevant.append(memory)

    return relevant
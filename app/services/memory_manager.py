from app.models import Memory
from app.ai_service import extract_memory
from app.services.memory_classifier import (
    classify_memory,
)


def save_memories(
    db,
    username: str,
    message: str,
):

    extracted_memory = extract_memory(
        message
    )
    classified_memory = classify_memory(
        extracted_memory
    )

    for category in classified_memory.values():

        for key, value in category.items():

            existing_memory = (
                db.query(Memory)
                .filter(
                    Memory.username == username,
                    Memory.key == key,
                )
                .first()
            )

            if existing_memory:

                existing_memory.value = value

            else:

                db.add(
                    Memory(
                        username=username,
                        key=key,
                        value=value,
                    )
                )
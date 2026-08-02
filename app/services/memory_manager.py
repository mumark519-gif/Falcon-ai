from app.models import Memory
from app.ai_service import extract_memory
from app.services.memory_classifier import (
    classify_memory,
)
from app.services.embedding_service import (
    create_embedding,
)


def save_memories(
    db,
    username: str,
    message: str,
):

    extracted_memory = extract_memory(
        message
    )

    memory_embeddings = {}

    for key, value in extracted_memory.items():

        memory_embeddings[key] = create_embedding(
            str(value)
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
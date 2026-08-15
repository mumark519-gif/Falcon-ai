from app.models import Memory
from app.ai_service import extract_memory
from datetime import datetime, timezone
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

                existing_memory.updated_at = datetime.now(timezone.utc)

                existing_memory.access_count += 1

                existing_memory.confidence = 100

            else:

                db.add(
                    Memory(
                        username=username,
                        key=key,
                        value=value,

                        category="general",

                        importance=5,

                        confidence=100,

                        access_count=1,

                        created_at=datetime.now(timezone.utc),

                        updated_at=datetime.now(timezone.utc),
                    )
                )
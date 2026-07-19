from sqlalchemy.orm import Session

from app.services.memory_service import search_memories
from app.services.vector_service import search_documents

from app.models import (
    Conversation,
    Chat,
    Memory,
)

from app.ai_service import (
    ask_ai,
    extract_memory,
    generate_chat_title,
)


def chat(
    request,
    current_user: str,
    db: Session,
):

    # Save user message
    db.add(
        Conversation(
            username=current_user,
            chat_id=request.chat_id,
            role="user",
            message=request.message,
        )
    )

    db.commit()

    # Load chat history
    messages = (
        db.query(Conversation)
        .filter(
            Conversation.username == current_user,
            Conversation.chat_id == request.chat_id,
        )
        .order_by(Conversation.id)
        .all()
    )

    # Load memories
    memories = search_memories(
        current_user,
        request.message,
    )

    # Build prompt
    prompt = "You are Falcon AI.\n\n"

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

    # Search uploaded documents
    knowledge = search_documents(
        current_user,
        request.message,
    )

    if knowledge:

        prompt += (
            "\n\nRelevant knowledge "
            "from uploaded documents:\n"
        )

        prompt += knowledge

    # Ask AI
    answer = ask_ai(prompt)

    # Extract memory
    extracted_memory = extract_memory(
        request.message
    )

    # Save memory
    for key, value in extracted_memory.items():

        existing_memory = (
            db.query(Memory)
            .filter(
                Memory.username == current_user,
                Memory.key == key,
            )
            .first()
        )

        if existing_memory:

            existing_memory.value = value

        else:

            db.add(
                Memory(
                    username=current_user,
                    key=key,
                    value=value,
                )
            )

    # Generate chat title
    chat_record = (
        db.query(Chat)
        .filter(
            Chat.id == request.chat_id,
            Chat.username == current_user,
        )
        .first()
    )

    if (
        chat_record
        and chat_record.title == "New Chat"
    ):

        chat_record.title = (
            generate_chat_title(
                request.message
            )
        )

    # Save AI response
    db.add(
        Conversation(
            username=current_user,
            chat_id=request.chat_id,
            role="assistant",
            message=answer,
        )
    )

    db.commit()

    return {
        "response": answer
    }
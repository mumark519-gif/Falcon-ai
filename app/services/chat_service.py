from app.services.memory_service import search_memories
from app.services.vector_service import search_documents
from app.database import SessionLocal
from app.models import Conversation, Chat, Memory
from app.ai_service import (
    ask_ai,
    extract_memory,
    generate_chat_title,
)

def chat(request, current_user):

    db = SessionLocal()

    # Save user message
    db.add(
        Conversation(
            username=current_user,
            chat_id=request.chat_id,
            role="user",
            message=request.message
        )
    )

    db.commit()

    # Load chat history
    messages = (
        db.query(Conversation)
        .filter(
            Conversation.username == current_user,
            Conversation.chat_id == request.chat_id
        )
        .order_by(Conversation.id)
        .all()
    )

    # Load memories
    
    memories = search_memories(
    current_user,
    request.message
    )

    # Build prompt
    prompt = "You are Falcon AI.\n\n"


    if memories:
      

      prompt += "Known information about the user:\n"

      for memory in memories:
          prompt += f"{memory.key}: {memory.value}\n"

      prompt += "\n"

    prompt += "Conversation:\n"

    for msg in messages:
       prompt += f"{msg.role}: {msg.message}\n"

    # Ask AI
    knowledge = search_documents(
        current_user,
        request.message
    )
    if knowledge:

        prompt += "\n\nRelevant knowledge from uploaded documents:\n"

        prompt += knowledge
    answer = ask_ai(prompt)

    # Extract memory
    memory = extract_memory(request.message)

    print("========== MEMORY ==========")
    print(memory)

    # Save memory
    for key, value in memory.items():

        existing_memory = (
            db.query(Memory)
            .filter(
                Memory.username == current_user,
                Memory.key == key
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
                    value=value
                )
            )
    # Generate chat title
    chat = (
        db.query(Chat)
        .filter(
            Chat.id == request.chat_id,
            Chat.username == current_user
        )
        .first()
    )

    if chat and chat.title == "New Chat":
        chat.title = generate_chat_title(request.message)

    db.commit()

    # Save AI response
    db.add(
        Conversation(
            username=current_user,
            chat_id=request.chat_id,
            role="assistant",
            message=answer
        )
    )

    db.commit()

    db.close()

    return {
        "response": answer
    }
from sqlalchemy.orm import Session
from app.core.logger import logger
from app.services.memory_service import search_memories
from app.services.vector_service import search_documents
from app.agents.planner import create_plan
import time

from app.models import (
    Chat,
)

from app.ai_service import (
    generate_chat_title,
)
from app.services.chat_manager import (
    update_chat_title,
)
from app.services.chat_history_manager import (
    load_chat_history,
)
from app.services.conversation_manager import (
    save_message,
)
from app.services.prompt_builder import (
    build_prompt,
)
from app.services.memory_manager import (
    save_memories,
)

from app.agents.orchestrator import orchestrate


def chat(
    request,
    current_user: str,
    db: Session,
):
    start_time = time.perf_counter()

    # Save user message
    save_message(
        db=db,
        username=current_user,
        chat_id=request.chat_id,
        role="user",
        message=request.message,
    )
    logger.info(
        f"User '{current_user}' sent a message."
    )

    # Load chat history
    messages = load_chat_history(
        db=db,
        username=current_user,
        chat_id=request.chat_id,
    )

    # Load memories
    memories = search_memories(
        current_user,
        request.message,
    )

    # Create execution plan
    plan = create_plan(request.message)

    logger.info(
        "Execution plan created."
    )

    # Search uploaded documents
    knowledge = search_documents(
        current_user,
        request.message,
    )

    prompt = build_prompt(
        plan=plan,
        memories=memories,
        messages=messages,
        knowledge=knowledge,
    )

    logger.info(
        "Running Falcon Orchestrator..."
    )

    answer = orchestrate(
        db=db,
        username=current_user,
        question=prompt,
    )
    logger.info(
        "Falcon generated a response."
    )

    save_memories(
        db=db,
        username=current_user,
        message=request.message,
    )

    # Update chat title
    update_chat_title(
        db=db,
        username=current_user,
        chat_id=request.chat_id,
        first_message=request.message,
    )

    # Save AI response
    save_message(
        db=db,
        username=current_user,
        chat_id=request.chat_id,
        role="assistant",
        message=answer,
    )
    elapsed = time.perf_counter() - start_time

    logger.info(
        f"Request completed in {elapsed:.2f} seconds."
    )

    return {
        "response": answer
    }
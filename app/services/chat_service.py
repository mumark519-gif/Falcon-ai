from sqlalchemy.orm import Session
from app.core.logger import logger
from app.services.memory_service import search_memories
from app.services.vector_service import search_documents
from app.agents.planner import create_plan
from app.intelligence.model_router import model_router
from app.services.ai.providers import ProviderError
from app.enterprise.commercial import ensure_personal_organization, enforce_plan_limit, record_usage
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
from app.services.ai.gemini_provider import ask_gemini
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
    ensure_personal_organization(db, current_user)
    try:
        enforce_plan_limit(db, current_user)
    except PermissionError as exc:
        return {"response": str(exc), "routing": None, "error": "plan_limit"}

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
    plan_data = create_plan(request.message)

    logger.info(
        "Execution plan created."
    )

    # Search uploaded documents
    knowledge = search_documents(
        current_user,
        request.message,
    )

    prompt = build_prompt(
        plan=plan_data,
        memories=memories,
        messages=messages,
        knowledge=knowledge,
    )

    logger.info(
        "Running Falcon Orchestrator..."
    )

    orchestration = orchestrate(
        db=db,
        username=current_user,
        question=prompt,
    )

    routing = None

    if orchestration.get("error"):

        answer = orchestration["message"]

    else:

        # Route through the capability-aware model router instead of a
        # hardcoded provider, so AI_PROVIDER / task type (code, research,
        # etc.) actually determine which model answers.
        try:
            answer, decision = model_router.generate_with_meta(
                request.message,
                orchestration["synthesis_prompt"],
            )
            routing = {
                "provider": decision.provider,
                "model": decision.model,
            }
        except ProviderError as exc:
            logger.warning("No AI provider could complete chat request: %s", exc)
            answer = (
                "Falcon could not complete this request because no configured "
                "AI provider is currently available. Configure a provider API "
                "key or restore provider credits and try again."
            )
            routing = {"provider": None, "model": None}

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

    record_usage(
        db,
        username=current_user,
        provider=(routing or {}).get("provider"),
        model=(routing or {}).get("model"),
        kind="chat",
        duration_ms=elapsed * 1000,
    )

    logger.info(
        f"Request completed in {elapsed:.2f} seconds."
    )

    return {
        "response": answer,
        "routing": routing,
    }


def chat_stream(
    request,
    current_user: str,
    db: Session,
):
    """
    Same pipeline as chat(), but yields the final answer as text
    chunks as they're generated, then persists the full message
    once streaming completes.
    """
    save_message(
        db=db,
        username=current_user,
        chat_id=request.chat_id,
        role="user",
        message=request.message,
    )

    messages = load_chat_history(
        db=db,
        username=current_user,
        chat_id=request.chat_id,
    )

    memories = search_memories(
        current_user,
        request.message,
    )

    plan_data = create_plan(request.message)

    knowledge = search_documents(
        current_user,
        request.message,
    )

    prompt = build_prompt(
        plan=plan_data,
        memories=memories,
        messages=messages,
        knowledge=knowledge,
    )

    orchestration = orchestrate(
        db=db,
        username=current_user,
        question=prompt,
    )

    if orchestration.get("error"):
        answer = orchestration["message"]

        def _single_chunk():
            yield answer

        chunks = _single_chunk()
    else:
        # Resolve the routing decision up front so the client can display it.
        # The router itself performs provider failover if the selected backend
        # becomes unavailable during generation.
        try:
            decision = model_router.choose(request.message)

            def _routed_chunks():
                import json
                yield "__ROUTE__" + json.dumps(
                    {"provider": decision.provider, "model": decision.model}
                ) + "\n"
                yield from model_router.stream(
                    request.message,
                    orchestration["synthesis_prompt"],
                    provider=decision.provider,
                    model=decision.model,
                )
            chunks = _routed_chunks()
        except ProviderError:
            chunks = iter([
                "Falcon could not complete this request because no configured "
                "AI provider is currently available. Configure a provider API "
                "key or restore provider credits and try again."
            ])

    collected: list[str] = []

    def _generator():
        for chunk in chunks:
            # The routing header (if present) is protocol metadata for the
            # client, not part of the answer -- don't persist it.
            if not chunk.startswith("__ROUTE__"):
                collected.append(chunk)
            yield chunk

        full_answer = "".join(collected)

        save_memories(
            db=db,
            username=current_user,
            message=request.message,
        )

        update_chat_title(
            db=db,
            username=current_user,
            chat_id=request.chat_id,
            first_message=request.message,
        )

        save_message(
            db=db,
            username=current_user,
            chat_id=request.chat_id,
            role="assistant",
            message=full_answer,
        )

    return _generator()
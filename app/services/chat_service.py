from __future__ import annotations

import json
import time
from collections.abc import Iterator
from typing import Any

from sqlalchemy.orm import Session

from app.agents.orchestrator import orchestrate
from app.agents.planner import create_plan
from app.core.logger import logger
from app.enterprise.commercial import (
    ensure_personal_organization,
    enforce_plan_limit,
    record_usage,
)
from app.intelligence.model_router import model_router
from app.services.ai.providers import ProviderError
from app.services.chat_history_manager import load_chat_history
from app.services.chat_manager import update_chat_title
from app.services.conversation_manager import save_message
from app.services.memory_manager import save_memories
from app.services.memory_service import search_memories
from app.services.prompt_builder import build_prompt
from app.services.vector_service import search_documents


def _provider_error_response() -> dict[str, Any]:
    """Return Falcon's standard response when no AI provider is available."""
    return {
        "response": (
            "Falcon could not complete this request because no configured "
            "AI provider is currently available. Configure a provider API "
            "key or restore provider credits and try again."
        ),
        "routing": {
            "provider": None,
            "model": None,
        },
    }


def _prepare_chat_context(
    request: Any,
    current_user: str,
    db: Session,
) -> tuple[list[Any], Any, Any, str]:
    """
    Build the common context used by both normal and streaming chat.

    Returns:
        messages:
            Existing conversation history including the newly saved user
            message.

        memories:
            Relevant long-term memories.

        knowledge:
            Relevant uploaded-document knowledge.

        prompt:
            Final prompt passed into Falcon's orchestrator.
    """

    # Save the user message before loading history so the current request
    # becomes part of the context used by the model.
    save_message(
        db=db,
        username=current_user,
        chat_id=request.chat_id,
        role="user",
        message=request.message,
    )

    logger.info(
        "User '%s' sent a message.",
        current_user,
    )

    # Load conversation history.
    messages = load_chat_history(
        db=db,
        username=current_user,
        chat_id=request.chat_id,
    )

    # Retrieve relevant long-term memories.
    memories = search_memories(
        current_user,
        request.message,
    )

    # Create an execution plan for the request.
    plan_data = create_plan(request.message)

    logger.info("Execution plan created.")

    # Search the user's uploaded knowledge/documents.
    knowledge = search_documents(
        current_user,
        request.message,
    )

    # Build the complete prompt used by the orchestrator.
    prompt = build_prompt(
        plan=plan_data,
        memories=memories,
        messages=messages,
        knowledge=knowledge,
    )

    return messages, memories, knowledge, prompt


def _run_orchestration(
    prompt: str,
    current_user: str,
    db: Session,
) -> dict[str, Any]:
    """Run Falcon's orchestration layer."""

    logger.info("Running Falcon Orchestrator...")

    return orchestrate(
        db=db,
        username=current_user,
        question=prompt,
    )


def _persist_completed_chat(
    *,
    request: Any,
    current_user: str,
    db: Session,
    answer: str,
) -> None:
    """
    Persist the completed assistant response and related chat state.
    """

    # Save memories generated from the user's message.
    save_memories(
        db=db,
        username=current_user,
        message=request.message,
    )

    # Update the chat title using the first user message.
    update_chat_title(
        db=db,
        username=current_user,
        chat_id=request.chat_id,
        first_message=request.message,
    )

    # Save the final assistant response.
    save_message(
        db=db,
        username=current_user,
        chat_id=request.chat_id,
        role="assistant",
        message=answer,
    )


def chat(
    request: Any,
    current_user: str,
    db: Session,
) -> dict[str, Any]:
    """
    Execute a complete Falcon chat request.

    Pipeline:

        commercial checks
        -> user message
        -> history
        -> memories
        -> planner
        -> knowledge
        -> prompt
        -> orchestrator
        -> model router
        -> persistence
        -> usage tracking
    """

    start_time = time.perf_counter()

    # ------------------------------------------------------------------
    # Commercial / account controls
    # ------------------------------------------------------------------

    ensure_personal_organization(
        db,
        current_user,
    )

    try:
        enforce_plan_limit(
            db,
            current_user,
        )
    except PermissionError as exc:
        return {
            "response": str(exc),
            "routing": None,
            "error": "plan_limit",
        }

    try:
        # ------------------------------------------------------------------
        # Build Falcon context
        # ------------------------------------------------------------------

        _, _, _, prompt = _prepare_chat_context(
            request=request,
            current_user=current_user,
            db=db,
        )

        # ------------------------------------------------------------------
        # Orchestration
        # ------------------------------------------------------------------

        orchestration = _run_orchestration(
            prompt=prompt,
            current_user=current_user,
            db=db,
        )

        routing: dict[str, str | None] | None = None

        # ------------------------------------------------------------------
        # Orchestration failure
        # ------------------------------------------------------------------

        if orchestration.get("error"):
            answer = orchestration.get(
                "message",
                "Falcon could not complete this request.",
            )

        # ------------------------------------------------------------------
        # AI generation
        # ------------------------------------------------------------------

        else:
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
                logger.warning(
                    "No AI provider could complete chat request: %s",
                    exc,
                )

                answer = _provider_error_response()["response"]

                routing = {
                    "provider": None,
                    "model": None,
                }

        logger.info("Falcon generated a response.")

        # ------------------------------------------------------------------
        # Persistence
        # ------------------------------------------------------------------

        _persist_completed_chat(
            request=request,
            current_user=current_user,
            db=db,
            answer=answer,
        )

        # ------------------------------------------------------------------
        # Usage tracking
        # ------------------------------------------------------------------

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
            "Request completed in %.2f seconds.",
            elapsed,
        )

        return {
            "response": answer,
            "routing": routing,
        }

    except Exception:
        logger.exception(
            "Unexpected error while processing chat request for user '%s'.",
            current_user,
        )

        # Do not expose internal stack traces or implementation details
        # through the API.
        return {
            "response": (
                "Falcon encountered an unexpected error while processing "
                "your request. Please try again."
            ),
            "routing": None,
            "error": "internal_error",
        }


def chat_stream(
    request: Any,
    current_user: str,
    db: Session,
) -> Iterator[str]:
    """
    Streaming version of Falcon chat.

    The streaming path follows the same commercial and processing pipeline
    as normal chat, while yielding model output incrementally.

    A routing metadata frame is emitted before the answer:

        __ROUTE__{"provider":"...","model":"..."}\\n

    This frame is protocol metadata and must not be persisted as part of
    the assistant's answer.
    """

    start_time = time.perf_counter()

    # ------------------------------------------------------------------
    # Commercial / account controls
    # ------------------------------------------------------------------

    try:
        ensure_personal_organization(
            db,
            current_user,
        )

        enforce_plan_limit(
            db,
            current_user,
        )

    except PermissionError as exc:

        def _plan_limit_generator() -> Iterator[str]:
            yield str(exc)

        return _plan_limit_generator()

    # ------------------------------------------------------------------
    # Prepare common chat context
    # ------------------------------------------------------------------

    try:
        _, _, _, prompt = _prepare_chat_context(
            request=request,
            current_user=current_user,
            db=db,
        )

        # ------------------------------------------------------------------
        # Orchestration
        # ------------------------------------------------------------------

        orchestration = _run_orchestration(
            prompt=prompt,
            current_user=current_user,
            db=db,
        )

    except Exception:
        logger.exception(
            "Failed to prepare streaming chat request for user '%s'.",
            current_user,
        )

        def _preparation_error_generator() -> Iterator[str]:
            yield (
                "Falcon encountered an error while preparing your request. "
                "Please try again."
            )

        return _preparation_error_generator()

    # ------------------------------------------------------------------
    # Orchestration error
    # ------------------------------------------------------------------

    if orchestration.get("error"):

        answer = orchestration.get(
            "message",
            "Falcon could not complete this request.",
        )

        def _orchestration_error_generator() -> Iterator[str]:
            yield answer

            _persist_completed_chat(
                request=request,
                current_user=current_user,
                db=db,
                answer=answer,
            )

            elapsed = time.perf_counter() - start_time

            record_usage(
                db,
                username=current_user,
                provider=None,
                model=None,
                kind="chat",
                duration_ms=elapsed * 1000,
            )

        return _orchestration_error_generator()

    # ------------------------------------------------------------------
    # Model routing
    # ------------------------------------------------------------------

    try:
        decision = model_router.choose(
            request.message,
        )

    except ProviderError as exc:
        logger.warning(
            "No AI provider available for streaming request: %s",
            exc,
        )

        answer = _provider_error_response()["response"]

        def _provider_error_generator() -> Iterator[str]:
            yield answer

            _persist_completed_chat(
                request=request,
                current_user=current_user,
                db=db,
                answer=answer,
            )

            elapsed = time.perf_counter() - start_time

            record_usage(
                db,
                username=current_user,
                provider=None,
                model=None,
                kind="chat",
                duration_ms=elapsed * 1000,
            )

        return _provider_error_generator()

    except Exception:
        logger.exception(
            "Unexpected model-routing error for user '%s'.",
            current_user,
        )

        answer = (
            "Falcon could not select an available AI provider. "
            "Please try again."
        )

        def _routing_error_generator() -> Iterator[str]:
            yield answer

            _persist_completed_chat(
                request=request,
                current_user=current_user,
                db=db,
                answer=answer,
            )

            elapsed = time.perf_counter() - start_time

            record_usage(
                db,
                username=current_user,
                provider=None,
                model=None,
                kind="chat",
                duration_ms=elapsed * 1000,
            )

        return _routing_error_generator()

    # ------------------------------------------------------------------
    # Actual streaming generator
    # ------------------------------------------------------------------

    def _generator() -> Iterator[str]:
        collected: list[str] = []

        routing_provider: str | None = decision.provider
        routing_model: str | None = decision.model

        # Send routing information to the frontend.
        yield (
            "__ROUTE__"
            + json.dumps(
                {
                    "provider": routing_provider,
                    "model": routing_model,
                }
            )
            + "\n"
        )

        try:
            # ----------------------------------------------------------
            # Stream model response
            # ----------------------------------------------------------

            for chunk in model_router.stream(
                request.message,
                orchestration["synthesis_prompt"],
                provider=decision.provider,
                model=decision.model,
            ):
                if not chunk:
                    continue

                collected.append(chunk)

                yield chunk

            # ----------------------------------------------------------
            # Streaming completed successfully
            # ----------------------------------------------------------

            full_answer = "".join(collected)

            _persist_completed_chat(
                request=request,
                current_user=current_user,
                db=db,
                answer=full_answer,
            )

            elapsed = time.perf_counter() - start_time

            record_usage(
                db,
                username=current_user,
                provider=routing_provider,
                model=routing_model,
                kind="chat",
                duration_ms=elapsed * 1000,
            )

            logger.info(
                "Streaming request completed in %.2f seconds.",
                elapsed,
            )

        except ProviderError as exc:
            logger.warning(
                "Streaming provider failed for user '%s': %s",
                current_user,
                exc,
            )

            # Preserve whatever content was successfully generated before
            # the provider failed.
            partial_answer = "".join(collected)

            if partial_answer:
                fallback_message = (
                    "\n\nFalcon's AI provider stopped responding before "
                    "the response was completed."
                )
                yield fallback_message
                full_answer = partial_answer + fallback_message
            else:
                full_answer = _provider_error_response()["response"]
                yield full_answer

            _persist_completed_chat(
                request=request,
                current_user=current_user,
                db=db,
                answer=full_answer,
            )

            elapsed = time.perf_counter() - start_time

            record_usage(
                db,
                username=current_user,
                provider=routing_provider,
                model=routing_model,
                kind="chat",
                duration_ms=elapsed * 1000,
            )

        except Exception:
            logger.exception(
                "Unexpected error during streaming for user '%s'.",
                current_user,
            )

            partial_answer = "".join(collected)

            if partial_answer:
                error_message = (
                    "\n\nFalcon encountered an error while completing "
                    "this response."
                )
                yield error_message
                full_answer = partial_answer + error_message
            else:
                full_answer = (
                    "Falcon encountered an error while generating "
                    "your response. Please try again."
                )
                yield full_answer

            _persist_completed_chat(
                request=request,
                current_user=current_user,
                db=db,
                answer=full_answer,
            )

            elapsed = time.perf_counter() - start_time

            record_usage(
                db,
                username=current_user,
                provider=routing_provider,
                model=routing_model,
                kind="chat",
                duration_ms=elapsed * 1000,
            )

    return _generator()
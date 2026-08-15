from __future__ import annotations

from typing import Any, Callable

from app.core.logger import logger


MAX_EXECUTION_ROUNDS = 3


def _status(result: Any) -> str:
    if not isinstance(result, dict):
        return "success"

    return str(
        result.get("status", "")
    ).strip().lower()


def _successful(result: Any) -> bool:
    return _status(result) in {
        "success",
        "complete",
        "completed",
        "partial",
    }


def _failed(result: Any) -> bool:
    return _status(result) in {
        "error",
        "failed",
        "failure",
    }


def _extract_error(result: Any) -> str:
    if not isinstance(result, dict):
        return ""

    return str(
        result.get("error")
        or result.get("message")
        or ""
    ).strip()


def _build_observation(
    result: Any,
    round_number: int,
) -> dict[str, Any]:
    """
    Convert raw execution output into an explicit observation.
    """

    status = _status(result)

    observation = {
        "round": round_number,
        "status": status,
        "successful": _successful(result),
        "failed": _failed(result),
        "error": _extract_error(result),
        "result": result,
    }

    if isinstance(result, dict):

        observation["completed_steps"] = result.get(
            "completed_steps",
            0,
        )

        observation["failed_steps"] = result.get(
            "failed_steps",
            0,
        )

        observation["total_steps"] = result.get(
            "total_steps",
            0,
        )

    return observation


def _needs_recovery(
    observation: dict[str, Any],
) -> bool:
    """
    Determine whether execution should be recovered/retried.
    """

    if observation.get("successful"):
        return False

    if observation.get("failed"):
        return True

    status = observation.get(
        "status",
        "",
    )

    return status in {
        "partial",
        "blocked",
        "timeout",
        "incomplete",
    }


def _default_recovery(
    question: str,
    observation: dict[str, Any],
) -> dict[str, Any]:
    """
    Deterministic recovery decision.

    This intentionally does not call an LLM. Recovery must
    remain safe even when the AI provider is unavailable.
    """

    error = observation.get(
        "error",
        "",
    )

    result = observation.get(
        "result",
        {},
    )

    failed_steps = 0

    if isinstance(result, dict):
        failed_steps = int(
            result.get(
                "failed_steps",
                0,
            )
            or 0
        )

    if failed_steps > 0:

        return {
            "action": "retry",
            "reason": (
                "Execution contained failed steps."
            ),
            "error": error,
        }

    if observation.get("status") == "partial":

        return {
            "action": "retry",
            "reason": (
                "Execution completed only partially."
            ),
            "error": error,
        }

    return {
        "action": "stop",
        "reason": (
            "Execution did not produce a recoverable failure."
        ),
        "error": error,
    }


def execute_adaptively(
    *,
    username: str,
    question: str,
    plan: dict[str, Any],
    execute_fn: Callable[..., dict[str, Any]],
    recover_fn: Callable[
        [str, dict[str, Any], dict[str, Any]],
        dict[str, Any] | None,
    ] | None = None,
    verify_fn: Callable[
        [str, dict[str, Any]],
        dict[str, Any],
    ] | None = None,
    memories: list | None = None,
    use_web: bool = False,
    use_documents: bool = False,
) -> dict[str, Any]:
    """
    Execute Falcon work adaptively.

    Flow:

        plan
          ↓
        execute
          ↓
        observe
          ↓
        recover/retry if necessary
          ↓
        execute again
          ↓
        verify
          ↓
        final result
    """

    memories = memories or []

    history: list[dict[str, Any]] = []

    current_plan = plan

    for round_number in range(
        1,
        MAX_EXECUTION_ROUNDS + 1,
    ):

        logger.info(
            "Falcon adaptive execution round %s/%s.",
            round_number,
            MAX_EXECUTION_ROUNDS,
        )

        try:

            result = execute_fn(
                username=username,
                plan=current_plan,
                question=question,
                use_web=use_web,
                use_documents=use_documents,
                memories=memories,
            )

        except Exception as exc:

            logger.exception(
                "Adaptive execution round failed."
            )

            result = {
                "status": "error",
                "error": str(exc),
                "completed_steps": 0,
                "failed_steps": 1,
                "total_steps": len(
                    current_plan.get(
                        "steps",
                        [],
                    )
                ),
            }

        observation = _build_observation(
            result,
            round_number,
        )

        history.append(
            observation
        )

        # ----------------------------------------------------
        # Successful execution
        # ----------------------------------------------------

        if observation["successful"]:

            logger.info(
                "Falcon execution succeeded on round %s.",
                round_number,
            )

            verification = None

            if verify_fn is not None:

                try:

                    verification = verify_fn(
                        question,
                        result,
                    )

                except Exception as exc:

                    logger.exception(
                        "Execution verification failed."
                    )

                    verification = {
                        "verified": False,
                        "error": str(exc),
                    }

            if verification is None:

                verification = {
                    "verified": True,
                    "reason": (
                        "Execution completed successfully."
                    ),
                }

            verified = bool(
                verification.get(
                    "verified",
                    False,
                )
            )

            if verified:

                return {
                    "status": "verified",
                    "successful": True,
                    "result": result,
                    "verification": verification,
                    "history": history,
                    "rounds": round_number,
                    "final_plan": current_plan,
                }

            # Execution succeeded but verification failed.
            # Give recovery a chance.

            observation["verification_failed"] = True

        # ----------------------------------------------------
        # Stop if no recovery is possible
        # ----------------------------------------------------

        if not _needs_recovery(
            observation
        ) and not observation.get(
            "verification_failed",
            False,
        ):

            return {
                "status": observation["status"],
                "successful": False,
                "result": result,
                "verification": {
                    "verified": False,
                    "reason": (
                        "Execution did not produce a "
                        "recoverable state."
                    ),
                },
                "history": history,
                "rounds": round_number,
                "final_plan": current_plan,
            }

        # ----------------------------------------------------
        # Maximum rounds reached
        # ----------------------------------------------------

        if round_number >= MAX_EXECUTION_ROUNDS:

            logger.warning(
                "Falcon reached maximum adaptive "
                "execution rounds."
            )

            return {
                "status": "failed",
                "successful": False,
                "result": result,
                "verification": {
                    "verified": False,
                    "reason": (
                        "Maximum adaptive execution "
                        "rounds reached."
                    ),
                },
                "history": history,
                "rounds": round_number,
                "final_plan": current_plan,
            }

        # ----------------------------------------------------
        # Recovery / re-planning
        # ----------------------------------------------------

        recovery = None

        if recover_fn is not None:

            try:

                recovery = recover_fn(
                    question,
                    current_plan,
                    observation,
                )

            except Exception:

                logger.exception(
                    "Adaptive recovery function failed."
                )

        if not recovery:

            recovery = _default_recovery(
                question,
                observation,
            )

        action = str(
            recovery.get(
                "action",
                "stop",
            )
        ).strip().lower()

        logger.info(
            "Falcon recovery decision: %s",
            action,
        )

        if action == "stop":

            return {
                "status": "failed",
                "successful": False,
                "result": result,
                "recovery": recovery,
                "verification": {
                    "verified": False,
                },
                "history": history,
                "rounds": round_number,
                "final_plan": current_plan,
            }

        if action in {
            "retry",
            "replan",
        }:

            new_plan = recovery.get(
                "plan"
            )

            if isinstance(
                new_plan,
                dict,
            ):

                current_plan = new_plan

            # Otherwise retry the current plan.
            continue

        return {
            "status": "failed",
            "successful": False,
            "result": result,
            "recovery": recovery,
            "verification": {
                "verified": False,
            },
            "history": history,
            "rounds": round_number,
            "final_plan": current_plan,
        }
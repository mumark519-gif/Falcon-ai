from __future__ import annotations

import json
from typing import Any, Callable

from app.ai_service import ask_ai
from app.core.logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

MAX_TASK_ROUNDS = 10
MAX_CONSECUTIVE_FAILURES = 3
MAX_TASK_HISTORY = 50
MAX_OBSERVATION_SIZE = 12000


# ============================================================
# TASK STATES
# ============================================================

TASK_STATES = {
    "created",
    "planning",
    "executing",
    "observing",
    "recovering",
    "verifying",
    "completed",
    "failed",
    "blocked",
    "cancelled",
}


# ============================================================
# STATUS HELPERS
# ============================================================

def _status(result: Any) -> str:
    if not isinstance(result, dict):
        return "success"

    return str(
        result.get("status", "")
    ).strip().lower()


def _is_success(result: Any) -> bool:
    return _status(result) in {
        "success",
        "complete",
        "completed",
        "verified",
    }


def _is_failure(result: Any) -> bool:
    return _status(result) in {
        "error",
        "failed",
        "failure",
    }


def _is_blocked(result: Any) -> bool:
    return _status(result) in {
        "blocked",
        "permission_required",
        "waiting_for_permission",
    }


def _extract_error(result: Any) -> str:
    if not isinstance(result, dict):
        return ""

    return str(
        result.get("error")
        or result.get("message")
        or ""
    ).strip()


# ============================================================
# SAFE SERIALIZATION
# ============================================================

def _safe_json(
    value: Any,
    max_length: int | None = None,
) -> str:
    """
    Safely serialize arbitrary Falcon state.

    This prevents malformed objects from breaking the
    autonomous task loop.
    """

    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        )
    except Exception:
        text = str(value)

    if (
        max_length is not None
        and len(text) > max_length
    ):
        return text[:max_length]

    return text


# ============================================================
# OBSERVATION
# ============================================================

def _build_observation(
    result: Any,
    round_number: int,
) -> dict[str, Any]:
    """
    Convert execution output into a normalized observation.

    The autonomous engine never assumes that an execution
    result is successful merely because a function returned.
    """

    status = _status(result)

    observation = {
        "round": round_number,
        "status": status,
        "successful": _is_success(result),
        "failed": _is_failure(result),
        "blocked": _is_blocked(result),
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


# ============================================================
# TASK HISTORY
# ============================================================

def _append_history(
    history: list[dict[str, Any]],
    entry: dict[str, Any],
) -> None:
    """
    Keep task history bounded.
    """

    history.append(entry)

    if len(history) > MAX_TASK_HISTORY:

        del history[
            :-MAX_TASK_HISTORY
        ]


# ============================================================
# TASK CREATION
# ============================================================

def create_task(
    question: str,
    username: str = "",
    memories: list | None = None,
) -> dict[str, Any]:
    """
    Create the persistent state object for an autonomous task.
    """

    return {
        "task_id": None,
        "username": username,
        "question": str(
            question or ""
        ).strip(),
        "state": "created",
        "round": 0,
        "plan": {},
        "history": [],
        "observations": [],
        "recoveries": [],
        "verification": {},
        "result": None,
        "error": None,
        "memories": memories or [],
        "metadata": {},
    }


# ============================================================
# TASK IDENTIFICATION
# ============================================================

def _generate_task_id(
    question: str,
) -> str:
    """
    Generate a deterministic lightweight task identifier.

    A database-backed task ID can replace this later without
    changing the autonomous execution interface.
    """

    import hashlib

    normalized = str(
        question or ""
    ).strip().encode(
        "utf-8"
    )

    return (
        "falcon-"
        + hashlib.sha256(
            normalized
        ).hexdigest()[:16]
    )


# ============================================================
# TASK UNDERSTANDING
# ============================================================

def understand_task(
    question: str,
    memories: list | None = None,
) -> dict[str, Any]:
    """
    Convert the user's request into an explicit task objective.

    This is deliberately separate from planning.

    Planning decides HOW to accomplish the task.
    Understanding determines WHAT the task actually is.
    """

    question = str(
        question or ""
    ).strip()

    if not question:

        return {
            "valid": False,
            "objective": "",
            "deliverables": [],
            "constraints": [],
            "success_conditions": [],
            "confidence": 0.0,
        }

    prompt = """
You are Falcon AI's Task Understanding Engine.

Understand the user's requested task before execution.

Do not execute tools.

Do not answer the task.

Determine:

1. The actual objective.
2. Expected deliverables.
3. Important constraints.
4. Dependencies.
5. What would count as successful completion.
6. Whether the request requires multiple steps.
7. Any information that is genuinely missing.

Do not invent missing information.

Return ONLY valid JSON.

Format:

{
    "valid": true,
    "objective": "...",
    "deliverables": [],
    "constraints": [],
    "dependencies": [],
    "success_conditions": [],
    "missing_information": [],
    "multi_step": true,
    "confidence": 0.0
}
"""

    prompt += (
        "\n\nUSER REQUEST:\n"
        + question
    )

    prompt += (
        "\n\nRELEVANT MEMORY:\n"
        + _safe_json(
            memories or [],
            8000,
        )
    )

    try:

        response = ask_ai(
            prompt
        )

        text = str(
            response or ""
        ).strip()

        if text.startswith("```"):

            lines = text.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            text = "\n".join(
                lines
            ).strip()

        result = json.loads(
            text
        )

        if not isinstance(
            result,
            dict,
        ):
            raise ValueError(
                "Task understanding returned invalid data."
            )

        result.setdefault(
            "valid",
            True,
        )

        result.setdefault(
            "objective",
            question,
        )

        result.setdefault(
            "deliverables",
            [],
        )

        result.setdefault(
            "constraints",
            [],
        )

        result.setdefault(
            "dependencies",
            [],
        )

        result.setdefault(
            "success_conditions",
            [],
        )

        result.setdefault(
            "missing_information",
            [],
        )

        result.setdefault(
            "multi_step",
            True,
        )

        result.setdefault(
            "confidence",
            0.5,
        )

        return result

    except Exception as exc:

        logger.exception(
            "Falcon task understanding failed."
        )

        return {
            "valid": True,
            "objective": question,
            "deliverables": [],
            "constraints": [],
            "dependencies": [],
            "success_conditions": [
                "Directly satisfy the user's request."
            ],
            "missing_information": [],
            "multi_step": True,
            "confidence": 0.3,
            "error": str(exc),
        }


# ============================================================
# RECOVERY DECISION
# ============================================================

def decide_recovery(
    question: str,
    task: dict[str, Any],
    observation: dict[str, Any],
) -> dict[str, Any]:
    """
    Decide whether Falcon should retry, replan, ask permission,
    or stop.

    Recovery is model-assisted but constrained by deterministic
    safety rules.
    """

    if observation.get(
        "blocked"
    ):

        return {
            "action": "stop",
            "reason": (
                "Execution requires permission or "
                "is currently blocked."
            ),
        }

    failed = observation.get(
        "failed",
        False,
    )

    if not failed:

        return {
            "action": "stop",
            "reason": (
                "No recoverable execution failure detected."
            ),
        }

    if task.get(
        "consecutive_failures",
        0,
    ) >= MAX_CONSECUTIVE_FAILURES:

        return {
            "action": "stop",
            "reason": (
                "Maximum consecutive failures reached."
            ),
        }

    prompt = """
You are Falcon AI's Recovery Decision Engine.

An autonomous task execution step failed.

Determine the safest useful recovery action.

Allowed actions:

- retry
- replan
- stop

Rules:

- Retry when the failure appears temporary.
- Replan when the current plan is likely wrong or incomplete.
- Stop when recovery is unlikely to help.
- Never invent successful results.
- Do not claim that a task is complete.
- Do not request dangerous or unauthorized actions.

Return ONLY valid JSON.

Format:

{
    "action": "retry",
    "reason": "...",
    "plan": null,
    "confidence": 0.0
}
"""

    prompt += (
        "\n\nUSER REQUEST:\n"
        + question
    )

    prompt += (
        "\n\nCURRENT TASK:\n"
        + _safe_json(
            task,
            10000,
        )
    )

    prompt += (
        "\n\nFAILURE OBSERVATION:\n"
        + _safe_json(
            observation,
            10000,
        )
    )

    try:

        response = ask_ai(
            prompt
        )

        text = str(
            response or ""
        ).strip()

        if text.startswith("```"):

            lines = text.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            text = "\n".join(
                lines
            ).strip()

        recovery = json.loads(
            text
        )

        if not isinstance(
            recovery,
            dict,
        ):
            raise ValueError(
                "Invalid recovery response."
            )

    except Exception as exc:

        logger.exception(
            "Falcon recovery reasoning failed."
        )

        return {
            "action": "retry",
            "reason": (
                "Recovery reasoning failed; "
                "retrying the failed task step."
            ),
            "plan": None,
            "confidence": 0.2,
            "error": str(exc),
        }

    action = str(
        recovery.get(
            "action",
            "stop",
        )
    ).strip().lower()

    if action not in {
        "retry",
        "replan",
        "stop",
    }:

        action = "stop"

    recovery["action"] = action

    return recovery


# ============================================================
# FINAL TASK VERIFICATION
# ============================================================

def verify_task_completion(
    question: str,
    task: dict[str, Any],
    result: Any,
) -> dict[str, Any]:
    """
    Determine whether Falcon actually completed the requested
    task rather than merely completing its internal workflow.
    """

    if not isinstance(
        result,
        dict,
    ):

        return {
            "verified": False,
            "reason": (
                "Execution result is not structured."
            ),
        }

    status = _status(
        result
    )

    if status not in {
        "complete",
        "completed",
        "success",
        "verified",
    }:

        return {
            "verified": False,
            "reason": (
                f"Execution status was '{status}'."
            ),
        }

    failed_steps = int(
        result.get(
            "failed_steps",
            0,
        )
        or 0
    )

    total_steps = int(
        result.get(
            "total_steps",
            0,
        )
        or 0
    )

    completed_steps = int(
        result.get(
            "completed_steps",
            0,
        )
        or 0
    )

    if failed_steps > 0:

        return {
            "verified": False,
            "reason": (
                f"{failed_steps} execution step(s) failed."
            ),
        }

    if (
        total_steps > 0
        and completed_steps < total_steps
    ):

        return {
            "verified": False,
            "reason": (
                "Not all execution steps completed."
            ),
        }

    return {
        "verified": True,
        "reason": (
            "The autonomous execution completed "
            "without failed steps."
        ),
        "completed_steps": completed_steps,
        "total_steps": total_steps,
    }


# ============================================================
# AUTONOMOUS TASK ENGINE
# ============================================================

def execute_autonomous_task(
    *,
    username: str,
    question: str,
    plan_fn: Callable[..., dict[str, Any]],
    execute_fn: Callable[..., dict[str, Any]],
    verify_fn: Callable[
        [str, dict[str, Any], Any],
        dict[str, Any],
    ] | None = None,
    memories: list | None = None,
    use_web: bool = False,
    use_documents: bool = False,
    initial_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Falcon's autonomous coworker execution loop.

    Architecture:

        USER GOAL
            ↓
        UNDERSTAND
            ↓
        PLAN
            ↓
        EXECUTE
            ↓
        OBSERVE
            ↓
        VERIFY
            ↓
        COMPLETE
             OR
        RECOVER
            ↓
        RETRY / REPLAN
            ↓
        EXECUTE AGAIN

    The engine deliberately accepts plan_fn and execute_fn
    callbacks so it can connect to Falcon's existing planner
    and execution systems without duplicating them.
    """

    question = str(
        question or ""
    ).strip()

    if not question:

        return {
            "status": "failed",
            "successful": False,
            "error": (
                "Cannot execute an empty task."
            ),
        }

    memories = memories or []

    task = create_task(
        question=question,
        username=username,
        memories=memories,
    )

    task["task_id"] = _generate_task_id(
        question
    )

    task["state"] = "planning"

    history: list[dict[str, Any]] = []

    consecutive_failures = 0

    # ========================================================
    # UNDERSTAND TASK
    # ========================================================

    understanding = understand_task(
        question=question,
        memories=memories,
    )

    task["understanding"] = understanding

    if not understanding.get(
        "valid",
        True,
    ):

        task["state"] = "failed"

        task["error"] = (
            "Falcon could not understand the requested task."
        )

        return task

    # ========================================================
    # INITIAL PLAN
    # ========================================================

    if isinstance(
        initial_plan,
        dict,
    ) and initial_plan:

        current_plan = initial_plan

    else:

        try:

            current_plan = plan_fn(
                question=question,
                understanding=understanding,
                memories=memories,
            )

        except TypeError:

            # Compatibility with Falcon's current create_plan
            # interface: create_plan(question)

            current_plan = plan_fn(
                question
            )

        except Exception as exc:

            logger.exception(
                "Falcon autonomous planning failed."
            )

            task["state"] = "failed"
            task["error"] = str(exc)

            return task

    if not isinstance(
        current_plan,
        dict,
    ):

        current_plan = {
            "steps": [],
            "status": "invalid",
        }

    task["plan"] = current_plan

    # ========================================================
    # AUTONOMOUS ROUNDS
    # ========================================================

    for round_number in range(
        1,
        MAX_TASK_ROUNDS + 1,
    ):

        task["round"] = round_number
        task["state"] = "executing"

        logger.info(
            "Falcon autonomous task '%s' round %s/%s.",
            task["task_id"],
            round_number,
            MAX_TASK_ROUNDS,
        )

        # ----------------------------------------------------
        # EXECUTE
        # ----------------------------------------------------

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
                "Autonomous task execution failed."
            )

            result = {
                "status": "error",
                "successful": False,
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

        # ----------------------------------------------------
        # OBSERVE
        # ----------------------------------------------------

        task["state"] = "observing"

        observation = _build_observation(
            result=result,
            round_number=round_number,
        )

        task["observations"].append(
            observation
        )

        _append_history(
            history,
            observation,
        )

        # ----------------------------------------------------
        # BLOCKED
        # ----------------------------------------------------

        if observation.get(
            "blocked"
        ):

            task["state"] = "blocked"
            task["result"] = result

            return {
                "status": "blocked",
                "successful": False,
                "task": task,
                "result": result,
                "history": history,
            }

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

        if observation.get(
            "successful"
        ):

            task["state"] = "verifying"

            try:

                if verify_fn is not None:

                    verification = verify_fn(
                        question,
                        task,
                        result,
                    )

                else:

                    verification = verify_task_completion(
                        question,
                        task,
                        result,
                    )

            except Exception as exc:

                logger.exception(
                    "Autonomous task verification failed."
                )

                verification = {
                    "verified": False,
                    "reason": str(exc),
                }

            task["verification"] = (
                verification
            )

            # ------------------------------------------------
            # VERIFIED
            # ------------------------------------------------

            if verification.get(
                "verified",
                False,
            ):

                task["state"] = "completed"
                task["result"] = result
                task["consecutive_failures"] = 0

                logger.info(
                    "Falcon autonomous task '%s' completed.",
                    task["task_id"],
                )

                return {
                    "status": "completed",
                    "successful": True,
                    "task": task,
                    "result": result,
                    "verification": verification,
                    "history": history,
                    "rounds": round_number,
                    "final_plan": current_plan,
                }

            # Verification failed despite execution
            # appearing successful. Treat it as recoverable.

            observation[
                "verification_failed"
            ] = True

        # ----------------------------------------------------
        # FAILURE
        # ----------------------------------------------------

        consecutive_failures += 1

        task[
            "consecutive_failures"
        ] = consecutive_failures

        # ----------------------------------------------------
        # MAX FAILURE GUARD
        # ----------------------------------------------------

        if (
            consecutive_failures
            >= MAX_CONSECUTIVE_FAILURES
        ):

            task["state"] = "failed"
            task["result"] = result

            logger.warning(
                "Falcon autonomous task '%s' "
                "reached consecutive failure limit.",
                task["task_id"],
            )

            return {
                "status": "failed",
                "successful": False,
                "task": task,
                "result": result,
                "history": history,
                "rounds": round_number,
                "error": (
                    "Maximum consecutive task failures reached."
                ),
            }

        # ----------------------------------------------------
        # MAX ROUND GUARD
        # ----------------------------------------------------

        if round_number >= MAX_TASK_ROUNDS:

            task["state"] = "failed"
            task["result"] = result

            return {
                "status": "failed",
                "successful": False,
                "task": task,
                "result": result,
                "history": history,
                "rounds": round_number,
                "error": (
                    "Maximum autonomous task rounds reached."
                ),
            }

        # ----------------------------------------------------
        # RECOVERY
        # ----------------------------------------------------

        task["state"] = "recovering"

        recovery = decide_recovery(
            question=question,
            task=task,
            observation=observation,
        )

        task["recoveries"].append(
            recovery
        )

        _append_history(
            history,
            {
                "round": round_number,
                "type": "recovery",
                "recovery": recovery,
            },
        )

        action = str(
            recovery.get(
                "action",
                "stop",
            )
        ).strip().lower()

        # ----------------------------------------------------
        # STOP
        # ----------------------------------------------------

        if action == "stop":

            task["state"] = "failed"
            task["result"] = result

            return {
                "status": "failed",
                "successful": False,
                "task": task,
                "result": result,
                "recovery": recovery,
                "history": history,
                "rounds": round_number,
                "final_plan": current_plan,
            }

        # ----------------------------------------------------
        # REPLAN
        # ----------------------------------------------------

        if action == "replan":

            new_plan = recovery.get(
                "plan"
            )

            if isinstance(
                new_plan,
                dict,
            ):

                current_plan = new_plan

            else:

                try:

                    current_plan = plan_fn(
                        question=question,
                        understanding=understanding,
                        memories=memories,
                    )

                except TypeError:

                    current_plan = plan_fn(
                        question
                    )

                except Exception as exc:

                    logger.exception(
                        "Autonomous replanning failed."
                    )

                    task["state"] = "failed"
                    task["error"] = str(exc)

                    return {
                        "status": "failed",
                        "successful": False,
                        "task": task,
                        "history": history,
                        "rounds": round_number,
                        "error": str(exc),
                    }

                if not isinstance(
                    current_plan,
                    dict,
                ):

                    task["state"] = "failed"

                    return {
                        "status": "failed",
                        "successful": False,
                        "task": task,
                        "history": history,
                        "rounds": round_number,
                        "error": (
                            "Replanning produced an invalid plan."
                        ),
                    }

            task["plan"] = current_plan

        # ----------------------------------------------------
        # RETRY / REPLAN
        # ----------------------------------------------------

        task["state"] = "planning"

        continue

    # Defensive fallback.

    task["state"] = "failed"

    return {
        "status": "failed",
        "successful": False,
        "task": task,
        "history": history,
        "error": (
            "Autonomous execution exited unexpectedly."
        ),
    }
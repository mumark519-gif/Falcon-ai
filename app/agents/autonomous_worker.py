from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from app.core.logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_MAX_ROUNDS = 10
DEFAULT_MAX_FAILURES = 3


# ============================================================
# STATUS HELPERS
# ============================================================

SUCCESS_STATUSES = {
    "success",
    "complete",
    "completed",
    "verified",
}


FAILURE_STATUSES = {
    "error",
    "failed",
    "failure",
}


def _status(result: Any) -> str:
    """
    Safely extract an execution status.
    """

    if not isinstance(result, dict):
        return "success"

    return str(
        result.get(
            "status",
            "",
        )
    ).strip().lower()


def _successful(result: Any) -> bool:
    return _status(result) in SUCCESS_STATUSES


def _failed(result: Any) -> bool:
    return _status(result) in FAILURE_STATUSES


def _timestamp() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# WORKER STATE
# ============================================================

class WorkerState:
    """
    State container for one autonomous Falcon task.

    The state survives across worker rounds and gives Falcon
    an explicit execution history.
    """

    def __init__(
        self,
        task: str,
        max_rounds: int = DEFAULT_MAX_ROUNDS,
        max_failures: int = DEFAULT_MAX_FAILURES,
    ) -> None:

        self.task = str(
            task or ""
        ).strip()

        self.max_rounds = max(
            1,
            int(max_rounds),
        )

        self.max_failures = max(
            1,
            int(max_failures),
        )

        self.status = "created"

        self.round = 0

        self.failures = 0

        self.successes = 0

        self.history: list[
            dict[str, Any]
        ] = []

        self.last_result: Any = None

        self.started_at = _timestamp()

        self.finished_at: str | None = None

    # --------------------------------------------------------
    # Record execution
    # --------------------------------------------------------

    def record(
        self,
        result: Any,
    ) -> None:

        self.round += 1

        self.last_result = result

        successful = _successful(
            result
        )

        failed = _failed(
            result
        )

        if successful:

            self.successes += 1

        if failed:

            self.failures += 1

        self.history.append(
            {
                "round": self.round,
                "timestamp": _timestamp(),
                "status": _status(result),
                "successful": successful,
                "failed": failed,
                "result": result,
            }
        )

    # --------------------------------------------------------
    # Failure threshold
    # --------------------------------------------------------

    def failure_limit_reached(self) -> bool:

        return (
            self.failures
            >= self.max_failures
        )

    # --------------------------------------------------------
    # Round threshold
    # --------------------------------------------------------

    def round_limit_reached(self) -> bool:

        return (
            self.round
            >= self.max_rounds
        )

    # --------------------------------------------------------
    # Finish
    # --------------------------------------------------------

    def finish(
        self,
        status: str,
    ) -> None:

        self.status = status

        self.finished_at = _timestamp()

    # --------------------------------------------------------
    # Snapshot
    # --------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:

        return {
            "task": self.task,
            "status": self.status,
            "round": self.round,
            "max_rounds": self.max_rounds,
            "failures": self.failures,
            "max_failures": self.max_failures,
            "successes": self.successes,
            "history": list(
                self.history
            ),
            "last_result": self.last_result,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


# ============================================================
# AUTONOMOUS WORKER
# ============================================================

class AutonomousWorker:
    """
    Falcon's autonomous task worker.

    Responsibilities:

    1. Own a long-running task.
    2. Execute one round.
    3. Observe the result.
    4. Continue when appropriate.
    5. Stop after success.
    6. Stop after safety limits.
    7. Preserve complete execution history.

    Planning and actual tool execution remain external.

    This class is deliberately an execution coordinator,
    not a giant tool executor.
    """

    def __init__(
        self,
        execute_fn: Callable[..., dict[str, Any]],
        max_rounds: int = DEFAULT_MAX_ROUNDS,
        max_failures: int = DEFAULT_MAX_FAILURES,
    ) -> None:

        if not callable(
            execute_fn
        ):
            raise TypeError(
                "execute_fn must be callable."
            )

        self.execute_fn = execute_fn

        self.max_rounds = max(
            1,
            int(max_rounds),
        )

        self.max_failures = max(
            1,
            int(max_failures),
        )

    # --------------------------------------------------------
    # Execute worker
    # --------------------------------------------------------

    def run(
        self,
        *,
        username: str,
        task: str,
        plan: dict[str, Any],
        memories: list | None = None,
        use_web: bool = False,
        use_documents: bool = False,
        should_continue_fn: Callable[
            [WorkerState],
            bool,
        ] | None = None,
    ) -> dict[str, Any]:
        """
        Run one autonomous Falcon task.

        The worker keeps executing until:

        - execution succeeds
        - continuation policy says stop
        - maximum rounds are reached
        - maximum failures are reached
        - an unexpected worker error occurs
        """

        state = WorkerState(
            task=task,
            max_rounds=self.max_rounds,
            max_failures=self.max_failures,
        )

        state.status = "running"

        memories = memories or []

        current_plan = plan

        while True:

            # ------------------------------------------------
            # Safety limits
            # ------------------------------------------------

            if state.round_limit_reached():

                logger.warning(
                    "Falcon autonomous worker reached "
                    "maximum rounds."
                )

                state.finish(
                    "max_rounds_reached"
                )

                break

            if state.failure_limit_reached():

                logger.warning(
                    "Falcon autonomous worker reached "
                    "maximum failures."
                )

                state.finish(
                    "max_failures_reached"
                )

                break

            # ------------------------------------------------
            # Execute
            # ------------------------------------------------

            logger.info(
                "Falcon autonomous worker executing "
                "round %s.",
                state.round + 1,
            )

            try:

                result = self.execute_fn(
                    username=username,
                    plan=current_plan,
                    question=task,
                    use_web=use_web,
                    use_documents=use_documents,
                    memories=memories,
                )

            except Exception as exc:

                logger.exception(
                    "Falcon autonomous worker execution "
                    "failed."
                )

                result = {
                    "status": "error",
                    "error": str(exc),
                }

            state.record(
                result
            )

            # ------------------------------------------------
            # Successful execution
            # ------------------------------------------------

            if _successful(result):

                # If no continuation policy is supplied,
                # successful execution ends the task.

                if should_continue_fn is None:

                    state.finish(
                        "complete"
                    )

                    break

                try:

                    should_continue = bool(
                        should_continue_fn(
                            state
                        )
                    )

                except Exception:

                    logger.exception(
                        "Worker continuation policy failed."
                    )

                    should_continue = False

                if not should_continue:

                    state.finish(
                        "complete"
                    )

                    break

                # Continue with the same plan unless the
                # continuation policy modifies external state.

                continue

            # ------------------------------------------------
            # Failed execution
            # ------------------------------------------------

            if _failed(result):

                if state.failure_limit_reached():

                    state.finish(
                        "max_failures_reached"
                    )

                    break

                # A failed round does not automatically mean
                # the entire task has failed. The surrounding
                # adaptive execution system may already have
                # recovered internally.

                continue

            # ------------------------------------------------
            # Partial / blocked / unknown state
            # ------------------------------------------------

            if should_continue_fn is None:

                state.finish(
                    _status(result)
                    or "incomplete"
                )

                break

            try:

                should_continue = bool(
                    should_continue_fn(
                        state
                    )
                )

            except Exception:

                logger.exception(
                    "Worker continuation policy failed."
                )

                should_continue = False

            if not should_continue:

                state.finish(
                    _status(result)
                    or "incomplete"
                )

                break

        # ====================================================
        # FINAL RESULT
        # ====================================================

        return {
            "status": state.status,
            "successful": state.status == "complete",
            "task": task,
            "rounds": state.round,
            "failures": state.failures,
            "successes": state.successes,
            "result": state.last_result,
            "history": state.history,
            "state": state.snapshot(),
        }


# ============================================================
# FUNCTIONAL API
# ============================================================

def run_autonomous_worker(
    *,
    execute_fn: Callable[..., dict[str, Any]],
    username: str,
    task: str,
    plan: dict[str, Any],
    memories: list | None = None,
    use_web: bool = False,
    use_documents: bool = False,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    max_failures: int = DEFAULT_MAX_FAILURES,
    should_continue_fn: Callable[
        [WorkerState],
        bool,
    ] | None = None,
) -> dict[str, Any]:
    """
    Functional wrapper around AutonomousWorker.
    """

    worker = AutonomousWorker(
        execute_fn=execute_fn,
        max_rounds=max_rounds,
        max_failures=max_failures,
    )

    return worker.run(
        username=username,
        task=task,
        plan=plan,
        memories=memories,
        use_web=use_web,
        use_documents=use_documents,
        should_continue_fn=should_continue_fn,
    )


# ============================================================
# HEALTH CHECK
# ============================================================

def worker_health() -> dict[str, Any]:

    return {
        "status": "ok",
        "max_rounds": DEFAULT_MAX_ROUNDS,
        "max_failures": DEFAULT_MAX_FAILURES,
        "features": [
            "long_running_tasks",
            "execution_history",
            "failure_limits",
            "round_limits",
            "continuation_policy",
            "safe_stop",
        ],
    }
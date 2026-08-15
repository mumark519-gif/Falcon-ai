from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Any


# ============================================================
# TASK STATE STORE
# ============================================================
#
# Purpose:
#
# Falcon needs a persistent representation of an active task.
#
# This layer tracks:
#
# - task identity
# - user
# - original request
# - current state
# - current plan
# - execution history
# - observations
# - recoveries
# - verification
# - intermediate results
# - task metadata
#
# This is intentionally storage-backend independent.
#
# For now it uses an in-process store.
#
# Later, without changing the public interface, this can be
# backed by PostgreSQL / Redis / another durable store.
#
# ============================================================


# ============================================================
# CONSTANTS
# ============================================================

MAX_HISTORY = 100
MAX_OBSERVATIONS = 100
MAX_RECOVERIES = 50
MAX_EVENTS = 200


VALID_STATES = {
    "created",
    "understanding",
    "planning",
    "executing",
    "observing",
    "recovering",
    "verifying",
    "waiting",
    "completed",
    "failed",
    "blocked",
    "cancelled",
}


# ============================================================
# TIME
# ============================================================

def _now() -> str:
    """
    Return a UTC timestamp suitable for task state metadata.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# SAFE COPY
# ============================================================

def _copy(
    value: Any,
) -> Any:
    """
    Protect internal task state from accidental mutation.
    """

    try:
        return deepcopy(
            value
        )
    except Exception:
        return value


# ============================================================
# TASK STATE
# ============================================================

def create_task_state(
    *,
    task_id: str,
    username: str,
    question: str,
    memories: list | None = None,
) -> dict[str, Any]:
    """
    Create a complete Falcon task-state object.
    """

    timestamp = _now()

    state = {
        "task_id": str(
            task_id
        ),

        "username": str(
            username or ""
        ),

        "question": str(
            question or ""
        ).strip(),

        "state": "created",

        "created_at": timestamp,

        "updated_at": timestamp,

        "round": 0,

        "plan": {},

        "understanding": {},

        "observations": [],

        "recoveries": [],

        "verification": {},

        "result": None,

        "error": None,

        "memories": _copy(
            memories or []
        ),

        "history": [],

        "events": [],

        "metadata": {},

        "metrics": {
            "execution_rounds": 0,
            "completed_steps": 0,
            "failed_steps": 0,
            "total_steps": 0,
            "tool_calls": 0,
            "agent_calls": 0,
            "recovery_count": 0,
        },
    }

    return state


# ============================================================
# IN-MEMORY STORE
# ============================================================

class TaskStateStore:
    """
    Thread-safe task state store.

    This gives Falcon one consistent interface for task state.

    The implementation can later be replaced with PostgreSQL,
    Redis, or another durable backend without changing the
    rest of Falcon's task engine.
    """

    def __init__(
        self,
    ) -> None:

        self._tasks: dict[
            str,
            dict[str, Any],
        ] = {}

        self._lock = RLock()


    # ========================================================
    # CREATE
    # ========================================================

    def create(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Register a new task.
        """

        if not isinstance(
            state,
            dict,
        ):
            raise TypeError(
                "Task state must be a dictionary."
            )

        task_id = str(
            state.get(
                "task_id",
                "",
            )
        ).strip()

        if not task_id:
            raise ValueError(
                "Task ID is required."
            )

        with self._lock:

            if task_id in self._tasks:
                raise ValueError(
                    f"Task already exists: {task_id}"
                )

            state = _copy(
                state
            )

            state.setdefault(
                "created_at",
                _now(),
            )

            state["updated_at"] = _now()

            self._tasks[
                task_id
            ] = state

            return _copy(
                state
            )


    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        task_id: str,
    ) -> bool:
        """
        Determine whether a task exists.
        """

        task_id = str(
            task_id or ""
        ).strip()

        if not task_id:
            return False

        with self._lock:
            return task_id in self._tasks


    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        task_id: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve a task state.
        """

        task_id = str(
            task_id or ""
        ).strip()

        if not task_id:
            return None

        with self._lock:

            state = self._tasks.get(
                task_id
            )

            if state is None:
                return None

            return _copy(
                state
            )


    # ========================================================
    # REQUIRE
    # ========================================================

    def require(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """
        Retrieve a task or raise a clear error.
        """

        state = self.get(
            task_id
        )

        if state is None:
            raise KeyError(
                f"Task not found: {task_id}"
            )

        return state


    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        task_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update task fields.
        """

        if not isinstance(
            updates,
            dict,
        ):
            raise TypeError(
                "Task updates must be a dictionary."
            )

        task_id = str(
            task_id or ""
        ).strip()

        with self._lock:

            if task_id not in self._tasks:
                raise KeyError(
                    f"Task not found: {task_id}"
                )

            state = self._tasks[
                task_id
            ]

            for key, value in updates.items():

                if key == "state":

                    value = str(
                        value or ""
                    ).strip().lower()

                    if value not in VALID_STATES:

                        raise ValueError(
                            f"Invalid task state: {value}"
                        )

                state[key] = _copy(
                    value
                )

            state["updated_at"] = _now()

            return _copy(
                state
            )


    # ========================================================
    # STATE
    # ========================================================

    def set_state(
        self,
        task_id: str,
        state_name: str,
    ) -> dict[str, Any]:
        """
        Change the current task state.
        """

        state_name = str(
            state_name or ""
        ).strip().lower()

        if state_name not in VALID_STATES:
            raise ValueError(
                f"Invalid task state: {state_name}"
            )

        return self.update(
            task_id,
            {
                "state": state_name,
            },
        )


    # ========================================================
    # ROUND
    # ========================================================

    def set_round(
        self,
        task_id: str,
        round_number: int,
    ) -> dict[str, Any]:
        """
        Update the autonomous execution round.
        """

        try:
            round_number = int(
                round_number
            )
        except (
            TypeError,
            ValueError,
        ):
            round_number = 0

        return self.update(
            task_id,
            {
                "round": max(
                    0,
                    round_number,
                ),
            },
        )


    # ========================================================
    # PLAN
    # ========================================================

    def set_plan(
        self,
        task_id: str,
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Store the current execution plan.
        """

        if not isinstance(
            plan,
            dict,
        ):
            raise TypeError(
                "Task plan must be a dictionary."
            )

        return self.update(
            task_id,
            {
                "plan": plan,
            },
        )


    # ========================================================
    # UNDERSTANDING
    # ========================================================

    def set_understanding(
        self,
        task_id: str,
        understanding: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Store Falcon's task understanding.
        """

        if not isinstance(
            understanding,
            dict,
        ):
            raise TypeError(
                "Task understanding must be a dictionary."
            )

        return self.update(
            task_id,
            {
                "understanding": understanding,
            },
        )


    # ========================================================
    # OBSERVATION
    # ========================================================

    def add_observation(
        self,
        task_id: str,
        observation: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Append an execution observation.
        """

        if not isinstance(
            observation,
            dict,
        ):
            raise TypeError(
                "Observation must be a dictionary."
            )

        with self._lock:

            state = self.require(
                task_id
            )

            observations = state.get(
                "observations",
                [],
            )

            observations.append(
                _copy(
                    observation
                )
            )

            observations = observations[
                -MAX_OBSERVATIONS:
            ]

            return self.update(
                task_id,
                {
                    "observations": observations,
                },
            )


    # ========================================================
    # RECOVERY
    # ========================================================

    def add_recovery(
        self,
        task_id: str,
        recovery: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Append a recovery decision.
        """

        if not isinstance(
            recovery,
            dict,
        ):
            raise TypeError(
                "Recovery must be a dictionary."
            )

        with self._lock:

            state = self.require(
                task_id
            )

            recoveries = state.get(
                "recoveries",
                [],
            )

            recoveries.append(
                _copy(
                    recovery
                )
            )

            recoveries = recoveries[
                -MAX_RECOVERIES:
            ]

            return self.update(
                task_id,
                {
                    "recoveries": recoveries,
                },
            )


    # ========================================================
    # VERIFICATION
    # ========================================================

    def set_verification(
        self,
        task_id: str,
        verification: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Store task verification state.
        """

        if not isinstance(
            verification,
            dict,
        ):
            raise TypeError(
                "Verification must be a dictionary."
            )

        return self.update(
            task_id,
            {
                "verification": verification,
            },
        )


    # ========================================================
    # RESULT
    # ========================================================

    def set_result(
        self,
        task_id: str,
        result: Any,
    ) -> dict[str, Any]:
        """
        Store the latest task result.
        """

        return self.update(
            task_id,
            {
                "result": result,
            },
        )


    # ========================================================
    # ERROR
    # ========================================================

    def set_error(
        self,
        task_id: str,
        error: Any,
    ) -> dict[str, Any]:
        """
        Store the current task error.
        """

        return self.update(
            task_id,
            {
                "error": str(
                    error or ""
                ),
            },
        )


    # ========================================================
    # HISTORY
    # ========================================================

    def add_history(
        self,
        task_id: str,
        entry: Any,
    ) -> dict[str, Any]:
        """
        Append an item to task history.
        """

        with self._lock:

            state = self.require(
                task_id
            )

            history = state.get(
                "history",
                [],
            )

            history.append(
                _copy(
                    entry
                )
            )

            history = history[
                -MAX_HISTORY:
            ]

            return self.update(
                task_id,
                {
                    "history": history,
                },
            )


    # ========================================================
    # EVENTS
    # ========================================================

    def add_event(
        self,
        task_id: str,
        event_type: str,
        data: Any = None,
    ) -> dict[str, Any]:
        """
        Append a structured task event.

        Events provide a clean audit trail for future UI,
        notifications, debugging, and analytics.
        """

        event = {
            "type": str(
                event_type or ""
            ).strip(),

            "timestamp": _now(),

            "data": _copy(
                data
            ),
        }

        with self._lock:

            state = self.require(
                task_id
            )

            events = state.get(
                "events",
                [],
            )

            events.append(
                event
            )

            events = events[
                -MAX_EVENTS:
            ]

            return self.update(
                task_id,
                {
                    "events": events,
                },
            )


    # ========================================================
    # METRICS
    # ========================================================

    def update_metrics(
        self,
        task_id: str,
        **metrics: Any,
    ) -> dict[str, Any]:
        """
        Update task metrics without replacing the whole
        metrics dictionary.
        """

        with self._lock:

            state = self.require(
                task_id
            )

            current = state.get(
                "metrics",
                {},
            )

            if not isinstance(
                current,
                dict,
            ):
                current = {}

            current.update(
                {
                    key: _copy(value)
                    for key, value
                    in metrics.items()
                }
            )

            return self.update(
                task_id,
                {
                    "metrics": current,
                },
            )


    # ========================================================
    # METRIC INCREMENT
    # ========================================================

    def increment_metric(
        self,
        task_id: str,
        metric: str,
        amount: int = 1,
    ) -> dict[str, Any]:
        """
        Increment a numeric task metric.
        """

        with self._lock:

            state = self.require(
                task_id
            )

            metrics = state.get(
                "metrics",
                {},
            )

            if not isinstance(
                metrics,
                dict,
            ):
                metrics = {}

            current = metrics.get(
                metric,
                0,
            )

            try:
                current = int(
                    current
                )
            except (
                TypeError,
                ValueError,
            ):
                current = 0

            try:
                amount = int(
                    amount
                )
            except (
                TypeError,
                ValueError,
            ):
                amount = 1

            metrics[
                metric
            ] = current + amount

            return self.update(
                task_id,
                {
                    "metrics": metrics,
                },
            )


    # ========================================================
    # COMPLETE
    # ========================================================

    def complete(
        self,
        task_id: str,
        result: Any = None,
        verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Mark a task as successfully completed.
        """

        updates = {
            "state": "completed",
            "result": result,
            "error": None,
        }

        if verification is not None:
            updates[
                "verification"
            ] = verification

        return self.update(
            task_id,
            updates,
        )


    # ========================================================
    # FAIL
    # ========================================================

    def fail(
        self,
        task_id: str,
        error: Any,
        result: Any = None,
    ) -> dict[str, Any]:
        """
        Mark a task as failed.
        """

        return self.update(
            task_id,
            {
                "state": "failed",
                "error": str(
                    error or ""
                ),
                "result": result,
            },
        )


    # ========================================================
    # BLOCK
    # ========================================================

    def block(
        self,
        task_id: str,
        reason: Any,
    ) -> dict[str, Any]:
        """
        Mark a task as blocked.
        """

        return self.update(
            task_id,
            {
                "state": "blocked",
                "error": str(
                    reason or ""
                ),
            },
        )


    # ========================================================
    # CANCEL
    # ========================================================

    def cancel(
        self,
        task_id: str,
        reason: Any = "",
    ) -> dict[str, Any]:
        """
        Mark a task as cancelled.
        """

        return self.update(
            task_id,
            {
                "state": "cancelled",
                "error": str(
                    reason or ""
                ),
            },
        )


    # ========================================================
    # LIST TASKS
    # ========================================================

    def list_tasks(
        self,
        username: str | None = None,
        states: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Return task snapshots.

        Useful later for Falcon's frontend task dashboard.
        """

        username = (
            str(username).strip()
            if username is not None
            else None
        )

        with self._lock:

            results = []

            for state in self._tasks.values():

                if (
                    username is not None
                    and state.get(
                        "username"
                    ) != username
                ):
                    continue

                if (
                    states is not None
                    and state.get(
                        "state"
                    ) not in states
                ):
                    continue

                results.append(
                    _copy(
                        state
                    )
                )

            return results


    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        task_id: str,
    ) -> bool:
        """
        Remove a task from the current store.

        This will later be restricted/disabled for durable
        production history if required.
        """

        task_id = str(
            task_id or ""
        ).strip()

        with self._lock:

            if task_id not in self._tasks:
                return False

            del self._tasks[
                task_id
            ]

            return True


    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """
        Clear all in-memory task state.

        Primarily useful for development/testing.
        """

        with self._lock:
            self._tasks.clear()


# ============================================================
# GLOBAL TASK STORE
# ============================================================

task_store = TaskStateStore()
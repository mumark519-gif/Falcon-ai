from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _copy(value: Any) -> Any:
    try:
        return deepcopy(value)
    except Exception:
        return value


class TaskStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    READY = "ready"
    RUNNING = "running"
    WAITING_PERMISSION = "waiting_permission"
    WAITING_INPUT = "waiting_input"
    PAUSED = "paused"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskState:
    """
    Persistent in-memory representation of a Falcon Worker task.

    This object represents WHAT Falcon is currently doing,
    independently from HOW a specific tool or agent performs it.

    Later systems can persist this state in PostgreSQL/Redis/etc.
    without changing the task model itself.
    """

    def __init__(
        self,
        task_id: str,
        username: str,
        request: str,
        *,
        conversation_id: str = "",
        priority: TaskPriority | str = TaskPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
    ) -> None:

        task_id = str(task_id or "").strip()

        if not task_id:
            raise ValueError("task_id is required.")

        self.task_id = task_id

        self.username = str(
            username or ""
        ).strip()

        self.conversation_id = str(
            conversation_id or ""
        ).strip()

        self.request = str(
            request or ""
        ).strip()

        self.status = TaskStatus.CREATED

        self.priority = self._normalize_priority(
            priority
        )

        self.created_at = _now()
        self.updated_at = self.created_at

        self.started_at: str | None = None
        self.completed_at: str | None = None

        self.current_step = 0
        self.total_steps = 0

        self.progress = 0.0

        self.plan: dict[str, Any] = {}

        self.step_states: list[
            dict[str, Any]
        ] = []

        self.results: list[
            dict[str, Any]
        ] = []

        self.errors: list[
            dict[str, Any]
        ] = []

        self.permissions: list[
            dict[str, Any]
        ] = []

        self.pending_permission: dict[
            str, Any
        ] | None = None

        self.pending_input: dict[
            str, Any
        ] | None = None

        self.recovery_attempts = 0

        self.max_recovery_attempts = 3

        self.cancel_requested = False

        self.metadata = _copy(
            metadata or {}
        )

        self._lock = RLock()

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_priority(
        priority: TaskPriority | str,
    ) -> TaskPriority:

        if isinstance(
            priority,
            TaskPriority,
        ):
            return priority

        value = str(
            priority or ""
        ).strip().lower()

        try:
            return TaskPriority(value)
        except ValueError:
            return TaskPriority.NORMAL

    # ========================================================
    # STATUS
    # ========================================================

    def set_status(
        self,
        status: TaskStatus | str,
    ) -> TaskStatus:

        if isinstance(
            status,
            TaskStatus,
        ):
            normalized = status
        else:

            value = str(
                status or ""
            ).strip().lower()

            try:
                normalized = TaskStatus(value)
            except ValueError:
                raise ValueError(
                    f"Invalid task status: {status}"
                )

        with self._lock:

            self.status = normalized

            if normalized == TaskStatus.RUNNING:

                if self.started_at is None:
                    self.started_at = _now()

            if normalized in {
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            }:

                self.completed_at = _now()

            self.updated_at = _now()

        return normalized

    def is_terminal(self) -> bool:

        with self._lock:

            return self.status in {
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            }

    # ========================================================
    # PLAN
    # ========================================================

    def set_plan(
        self,
        plan: dict[str, Any],
    ) -> None:

        if not isinstance(
            plan,
            dict,
        ):
            raise TypeError(
                "Task plan must be a dictionary."
            )

        with self._lock:

            self.plan = _copy(plan)

            steps = plan.get(
                "steps",
                [],
            )

            if isinstance(
                steps,
                list,
            ):

                self.total_steps = len(
                    steps
                )

                self.step_states = [
                    {
                        "index": index,
                        "status": "pending",
                        "result": None,
                        "error": None,
                        "started_at": None,
                        "completed_at": None,
                    }
                    for index in range(
                        1,
                        len(steps) + 1,
                    )
                ]

            self.updated_at = _now()

    def get_plan(self) -> dict[str, Any]:

        with self._lock:
            return _copy(
                self.plan
            )

    # ========================================================
    # STEP STATE
    # ========================================================

    def start_step(
        self,
        step_index: int,
    ) -> None:

        with self._lock:

            if step_index < 1:
                raise ValueError(
                    "Step index must start at 1."
                )

            self.current_step = step_index

            if self.total_steps > 0:

                self.progress = min(
                    1.0,
                    max(
                        0.0,
                        (
                            step_index - 1
                        )
                        / self.total_steps,
                    ),
                )

            self._ensure_step(
                step_index
            )

            step = self.step_states[
                step_index - 1
            ]

            step["status"] = "running"
            step["started_at"] = _now()
            step["error"] = None

            self.status = TaskStatus.RUNNING

            if self.started_at is None:
                self.started_at = _now()

            self.updated_at = _now()

    def complete_step(
        self,
        step_index: int,
        result: Any = None,
    ) -> None:

        with self._lock:

            self._ensure_step(
                step_index
            )

            step = self.step_states[
                step_index - 1
            ]

            step["status"] = "completed"
            step["result"] = _copy(
                result
            )
            step["completed_at"] = _now()

            self.current_step = step_index

            if self.total_steps > 0:

                self.progress = min(
                    1.0,
                    step_index
                    / self.total_steps,
                )

            self.updated_at = _now()

    def fail_step(
        self,
        step_index: int,
        error: Any,
    ) -> None:

        with self._lock:

            self._ensure_step(
                step_index
            )

            message = str(
                error or ""
            ).strip()

            step = self.step_states[
                step_index - 1
            ]

            step["status"] = "failed"
            step["error"] = message
            step["completed_at"] = _now()

            self.errors.append(
                {
                    "type": "step",
                    "step_index": step_index,
                    "error": message,
                    "timestamp": _now(),
                }
            )

            self.updated_at = _now()

    def skip_step(
        self,
        step_index: int,
        reason: str = "",
    ) -> None:

        with self._lock:

            self._ensure_step(
                step_index
            )

            step = self.step_states[
                step_index - 1
            ]

            step["status"] = "skipped"
            step["error"] = reason
            step["completed_at"] = _now()

            self.updated_at = _now()

    def _ensure_step(
        self,
        step_index: int,
    ) -> None:

        while len(
            self.step_states
        ) < step_index:

            self.step_states.append(
                {
                    "index": len(
                        self.step_states
                    ) + 1,
                    "status": "pending",
                    "result": None,
                    "error": None,
                    "started_at": None,
                    "completed_at": None,
                }
            )

        if step_index > self.total_steps:
            self.total_steps = step_index

    # ========================================================
    # RESULTS
    # ========================================================

    def add_result(
        self,
        result_type: str,
        value: Any,
        *,
        step_index: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:

        result = {
            "type": str(
                result_type or ""
            ).strip(),

            "value": _copy(value),

            "step_index": step_index,

            "metadata": _copy(
                metadata or {}
            ),

            "timestamp": _now(),
        }

        with self._lock:

            self.results.append(
                result
            )

            self.updated_at = _now()

    # ========================================================
    # PERMISSIONS
    # ========================================================

    def request_permission(
        self,
        action: str,
        *,
        reason: str = "",
        details: Any = None,
        permission_type: str = "action",
    ) -> dict[str, Any]:

        request = {
            "action": str(
                action or ""
            ).strip(),

            "reason": str(
                reason or ""
            ).strip(),

            "details": _copy(
                details
            ),

            "permission_type": str(
                permission_type or "action"
            ).strip(),

            "status": "pending",

            "requested_at": _now(),
        }

        with self._lock:

            self.pending_permission = request

            self.permissions.append(
                request
            )

            self.status = (
                TaskStatus.WAITING_PERMISSION
            )

            self.updated_at = _now()

        return _copy(request)

    def resolve_permission(
        self,
        approved: bool,
        *,
        response: Any = None,
    ) -> None:

        with self._lock:

            if self.pending_permission is None:
                return

            self.pending_permission[
                "status"
            ] = (
                "approved"
                if approved
                else "denied"
            )

            self.pending_permission[
                "response"
            ] = _copy(response)

            self.pending_permission[
                "resolved_at"
            ] = _now()

            self.pending_permission = None

            if approved:

                self.status = TaskStatus.RUNNING

            else:

                self.status = TaskStatus.FAILED

            self.updated_at = _now()

    # ========================================================
    # USER INPUT
    # ========================================================

    def request_input(
        self,
        prompt: str,
        *,
        field: str = "",
        options: list[Any] | None = None,
    ) -> dict[str, Any]:

        request = {
            "prompt": str(
                prompt or ""
            ).strip(),

            "field": str(
                field or ""
            ).strip(),

            "options": _copy(
                options or []
            ),

            "status": "pending",

            "requested_at": _now(),
        }

        with self._lock:

            self.pending_input = request

            self.status = (
                TaskStatus.WAITING_INPUT
            )

            self.updated_at = _now()

        return _copy(request)

    def resolve_input(
        self,
        value: Any,
    ) -> None:

        with self._lock:

            if self.pending_input is None:
                return

            self.pending_input[
                "status"
            ] = "resolved"

            self.pending_input[
                "value"
            ] = _copy(value)

            self.pending_input[
                "resolved_at"
            ] = _now()

            self.pending_input = None

            self.status = TaskStatus.RUNNING

            self.updated_at = _now()

    # ========================================================
    # RECOVERY
    # ========================================================

    def start_recovery(
        self,
        reason: str = "",
    ) -> bool:

        with self._lock:

            if (
                self.recovery_attempts
                >= self.max_recovery_attempts
            ):
                return False

            self.recovery_attempts += 1

            self.status = (
                TaskStatus.RECOVERING
            )

            self.metadata[
                "last_recovery_reason"
            ] = str(
                reason or ""
            )

            self.updated_at = _now()

            return True

    # ========================================================
    # CANCELLATION
    # ========================================================

    def request_cancel(self) -> None:

        with self._lock:

            self.cancel_requested = True

            if not self.is_terminal():

                self.status = (
                    TaskStatus.CANCELLED
                )

            self.updated_at = _now()

    def cancellation_requested(self) -> bool:

        with self._lock:
            return self.cancel_requested

    # ========================================================
    # FINALIZATION
    # ========================================================

    def complete(
        self,
        result: Any = None,
    ) -> None:

        with self._lock:

            if result is not None:

                self.add_result(
                    "final",
                    result,
                )

            self.progress = 1.0

            self.status = TaskStatus.COMPLETED

            self.completed_at = _now()

            self.updated_at = _now()

    def fail(
        self,
        error: Any,
    ) -> None:

        with self._lock:

            message = str(
                error or ""
            ).strip()

            self.errors.append(
                {
                    "type": "task",
                    "error": message,
                    "timestamp": _now(),
                }
            )

            self.status = TaskStatus.FAILED

            self.completed_at = _now()

            self.updated_at = _now()

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(self) -> dict[str, Any]:

        with self._lock:

            return {
                "task_id": self.task_id,
                "username": self.username,
                "conversation_id": self.conversation_id,
                "request": self.request,

                "status": self.status.value,

                "priority": self.priority.value,

                "created_at": self.created_at,
                "updated_at": self.updated_at,

                "started_at": self.started_at,
                "completed_at": self.completed_at,

                "current_step": self.current_step,
                "total_steps": self.total_steps,
                "progress": self.progress,

                "plan": _copy(
                    self.plan
                ),

                "step_states": _copy(
                    self.step_states
                ),

                "results": _copy(
                    self.results
                ),

                "errors": _copy(
                    self.errors
                ),

                "permissions": _copy(
                    self.permissions
                ),

                "pending_permission": _copy(
                    self.pending_permission
                ),

                "pending_input": _copy(
                    self.pending_input
                ),

                "recovery_attempts": (
                    self.recovery_attempts
                ),

                "max_recovery_attempts": (
                    self.max_recovery_attempts
                ),

                "cancel_requested": (
                    self.cancel_requested
                ),

                "metadata": _copy(
                    self.metadata
                ),
            }


# ============================================================
# TASK STORE
# ============================================================


class TaskStore:
    """
    Central task registry.

    Later this can be backed by a database without changing
    the Worker API.
    """

    def __init__(self) -> None:

        self._tasks: dict[
            str,
            TaskState,
        ] = {}

        self._lock = RLock()

    def create(
        self,
        task_id: str,
        username: str,
        request: str,
        *,
        conversation_id: str = "",
        priority: TaskPriority | str = TaskPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
    ) -> TaskState:

        with self._lock:

            if task_id in self._tasks:

                raise ValueError(
                    f"Task already exists: {task_id}"
                )

            task = TaskState(
                task_id=task_id,
                username=username,
                request=request,
                conversation_id=conversation_id,
                priority=priority,
                metadata=metadata,
            )

            self._tasks[
                task_id
            ] = task

            return task

    def get(
        self,
        task_id: str,
    ) -> TaskState | None:

        with self._lock:

            return self._tasks.get(
                str(
                    task_id or ""
                ).strip()
            )

    def delete(
        self,
        task_id: str,
    ) -> bool:

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

    def all(
        self,
    ) -> list[TaskState]:

        with self._lock:
            return list(
                self._tasks.values()
            )

    def snapshots(
        self,
    ) -> list[dict[str, Any]]:

        return [
            task.snapshot()
            for task in self.all()
        ]

    def clear(self) -> None:

        with self._lock:
            self._tasks.clear()


task_store = TaskStore()
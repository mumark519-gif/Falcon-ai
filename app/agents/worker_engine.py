from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from app.core.logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

MAX_ACTIONS = 50
MAX_RETRIES_PER_ACTION = 2
DEFAULT_TIMEOUT = 300


# ============================================================
# TYPES
# ============================================================

@dataclass
class WorkerAction:
    """
    One executable action inside a Falcon task.
    """

    action_id: str
    name: str

    action_type: str = "tool"

    tool: str | None = None
    agent: str | None = None

    input: Any = None

    depends_on: list[str] = field(
        default_factory=list
    )

    requires_permission: bool = False

    status: str = "pending"

    result: Any = None
    error: str | None = None

    attempts: int = 0

    started_at: float | None = None
    finished_at: float | None = None


@dataclass
class WorkerTask:
    """
    Persistent conceptual representation of a Falcon task.
    """

    task_id: str

    username: str

    question: str

    status: str = "pending"

    actions: list[WorkerAction] = field(
        default_factory=list
    )

    current_action: str | None = None

    results: list[dict[str, Any]] = field(
        default_factory=list
    )

    errors: list[dict[str, Any]] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: float = field(
        default_factory=time.time
    )

    started_at: float | None = None
    finished_at: float | None = None


# ============================================================
# WORKER ENGINE
# ============================================================

class WorkerEngine:
    """
    Falcon's general-purpose task execution engine.

    The Worker is intentionally independent from specific tools.

    It can eventually execute:

        tools
        agents
        browser actions
        GitHub actions
        API actions
        file operations
        multimodal actions
        enterprise actions
        plugins
        autonomous workflows

    The worker manages:

        task state
        action dependencies
        permissions
        retries
        recovery
        cancellation
        progress
        results
    """

    def __init__(
        self,
        *,
        tool_executor: Callable[..., Any] | None = None,
        agent_executor: Callable[..., Any] | None = None,
        permission_checker: Callable[..., Any] | None = None,
        verifier: Callable[..., Any] | None = None,
    ):
        self.tool_executor = tool_executor
        self.agent_executor = agent_executor
        self.permission_checker = permission_checker
        self.verifier = verifier

        self.tasks: dict[str, WorkerTask] = {}

    # ========================================================
    # TASK CREATION
    # ========================================================

    def create_task(
        self,
        *,
        username: str,
        question: str,
        actions: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkerTask:
        """
        Create a new Falcon worker task.
        """

        task_id = str(
            uuid.uuid4()
        )

        task = WorkerTask(
            task_id=task_id,
            username=username,
            question=question,
            metadata=metadata or {},
        )

        if actions:

            task.actions = [
                self._normalize_action(
                    action,
                    index,
                )
                for index, action in enumerate(
                    actions,
                    start=1,
                )
            ]

        self.tasks[task_id] = task

        logger.info(
            "Falcon worker task created: %s",
            task_id,
        )

        return task

    # ========================================================
    # ACTION NORMALIZATION
    # ========================================================

    def _normalize_action(
        self,
        action: dict[str, Any],
        index: int,
    ) -> WorkerAction:
        """
        Convert planner/action output into a WorkerAction.
        """

        if not isinstance(
            action,
            dict,
        ):
            action = {}

        action_id = str(
            action.get(
                "action_id"
            )
            or action.get(
                "id"
            )
            or f"action_{index}"
        ).strip()

        name = str(
            action.get(
                "name"
            )
            or action.get(
                "task"
            )
            or action.get(
                "description"
            )
            or action_id
        ).strip()

        action_type = str(
            action.get(
                "action_type"
            )
            or action.get(
                "type"
            )
            or "tool"
        ).strip().lower()

        depends_on = action.get(
            "depends_on",
            [],
        )

        if not isinstance(
            depends_on,
            list,
        ):
            depends_on = [
                depends_on
            ]

        depends_on = [
            str(item).strip()
            for item in depends_on
            if str(item).strip()
        ]

        return WorkerAction(
            action_id=action_id,
            name=name,
            action_type=action_type,
            tool=(
                str(
                    action.get(
                        "tool"
                    )
                ).strip().lower()
                if action.get("tool")
                else None
            ),
            agent=(
                str(
                    action.get(
                        "agent"
                    )
                ).strip().upper()
                if action.get("agent")
                else None
            ),
            input=action.get(
                "input",
                action.get(
                    "task"
                ),
            ),
            depends_on=depends_on,
            requires_permission=bool(
                action.get(
                    "requires_permission",
                    False,
                )
            ),
        )

    # ========================================================
    # TASK LOOKUP
    # ========================================================

    def get_task(
        self,
        task_id: str,
    ) -> WorkerTask | None:
        """
        Retrieve a worker task.
        """

        return self.tasks.get(
            task_id
        )

    # ========================================================
    # PERMISSION
    # ========================================================

    def _check_permission(
        self,
        task: WorkerTask,
        action: WorkerAction,
    ) -> tuple[bool, str]:
        """
        Check whether an action may execute.
        """

        if not action.requires_permission:

            return (
                True,
                "Permission not required.",
            )

        if self.permission_checker is None:

            return (
                False,
                "User permission is required.",
            )

        try:

            result = self.permission_checker(
                task=task,
                action=action,
            )

        except Exception as exc:

            logger.exception(
                "Worker permission check failed."
            )

            return (
                False,
                str(exc),
            )

        if isinstance(
            result,
            dict,
        ):

            allowed = bool(
                result.get(
                    "allowed",
                    False,
                )
            )

            reason = str(
                result.get(
                    "reason",
                    "",
                )
                or ""
            )

            return (
                allowed,
                reason,
            )

        return (
            bool(result),
            "Permission evaluated.",
        )

    # ========================================================
    # DEPENDENCIES
    # ========================================================

    def _dependencies_satisfied(
        self,
        task: WorkerTask,
        action: WorkerAction,
    ) -> tuple[bool, str]:
        """
        Ensure all prerequisite actions completed.
        """

        if not action.depends_on:

            return (
                True,
                "",
            )

        action_map = {
            item.action_id: item
            for item in task.actions
        }

        for dependency_id in action.depends_on:

            dependency = action_map.get(
                dependency_id
            )

            if dependency is None:

                return (
                    False,
                    f"Missing dependency: {dependency_id}",
                )

            if dependency.status != "complete":

                return (
                    False,
                    (
                        f"Dependency '{dependency_id}' "
                        f"is not complete."
                    ),
                )

        return (
            True,
            "",
        )

    # ========================================================
    # ACTION EXECUTION
    # ========================================================

    def _execute_action(
        self,
        task: WorkerTask,
        action: WorkerAction,
    ) -> Any:
        """
        Execute one action through the appropriate executor.
        """

        if action.action_type == "tool":

            if self.tool_executor is None:

                raise RuntimeError(
                    "Worker tool executor is not configured."
                )

            return self.tool_executor(
                username=task.username,
                tool=action.tool,
                tool_input=action.input,
                task=task,
                action=action,
            )

        if action.action_type == "agent":

            if self.agent_executor is None:

                raise RuntimeError(
                    "Worker agent executor is not configured."
                )

            return self.agent_executor(
                username=task.username,
                agent=action.agent,
                task_input=action.input,
                task=task,
                action=action,
            )

        if action.action_type == "function":

            callable_target = action.input

            if not callable(
                callable_target
            ):

                raise RuntimeError(
                    "Function action does not contain "
                    "a callable target."
                )

            return callable_target()

        raise RuntimeError(
            f"Unsupported worker action type: "
            f"{action.action_type}"
        )

    # ========================================================
    # VERIFICATION
    # ========================================================

    def _verify_action(
        self,
        task: WorkerTask,
        action: WorkerAction,
        result: Any,
    ) -> tuple[bool, str]:
        """
        Verify the result of an action.
        """

        if self.verifier is None:

            return (
                True,
                "No action verifier configured.",
            )

        try:

            verification = self.verifier(
                task=task,
                action=action,
                result=result,
            )

        except Exception as exc:

            logger.exception(
                "Worker action verification failed."
            )

            return (
                False,
                str(exc),
            )

        if isinstance(
            verification,
            dict,
        ):

            return (
                bool(
                    verification.get(
                        "verified",
                        False,
                    )
                ),
                str(
                    verification.get(
                        "reason",
                        "",
                    )
                    or ""
                ),
            )

        return (
            bool(verification),
            "Action verification completed.",
        )

    # ========================================================
    # RECOVERY
    # ========================================================

    def _recover_action(
        self,
        task: WorkerTask,
        action: WorkerAction,
    ) -> bool:
        """
        Decide whether a failed action can be retried.
        """

        if action.attempts >= (
            MAX_RETRIES_PER_ACTION + 1
        ):

            return False

        action.status = "retrying"

        logger.warning(
            "Falcon worker retrying action '%s'.",
            action.action_id,
        )

        return True

    # ========================================================
    # ACTION EXECUTION LOOP
    # ========================================================

    def run_task(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """
        Execute a complete worker task.
        """

        task = self.tasks.get(
            task_id
        )

        if task is None:

            return {
                "status": "error",
                "error": "Worker task not found.",
            }

        if task.status == "cancelled":

            return self.snapshot(
                task_id
            )

        task.status = "running"
        task.started_at = time.time()

        logger.info(
            "Falcon worker started task %s.",
            task_id,
        )

        if len(task.actions) > MAX_ACTIONS:

            task.status = "failed"

            task.errors.append(
                {
                    "error": (
                        f"Task exceeds maximum allowed "
                        f"actions ({MAX_ACTIONS})."
                    )
                }
            )

            return self.snapshot(
                task_id
            )

        while True:

            pending_actions = [
                action
                for action in task.actions
                if action.status in {
                    "pending",
                    "retrying",
                }
            ]

            if not pending_actions:

                break

            progress_made = False

            for action in pending_actions:

                if task.status == "cancelled":

                    break

                dependencies_ok, dependency_error = (
                    self._dependencies_satisfied(
                        task,
                        action,
                    )
                )

                if not dependencies_ok:

                    # Dependency may simply be waiting for
                    # another action, so don't immediately fail.
                    if (
                        dependency_error
                        and dependency_error.startswith(
                            "Dependency '"
                        )
                    ):
                        continue

                    action.status = "failed"
                    action.error = dependency_error

                    task.errors.append(
                        {
                            "action_id": action.action_id,
                            "error": dependency_error,
                        }
                    )

                    progress_made = True

                    continue

                allowed, permission_reason = (
                    self._check_permission(
                        task,
                        action,
                    )
                )

                if not allowed:

                    action.status = (
                        "permission_required"
                    )

                    action.error = permission_reason

                    task.errors.append(
                        {
                            "action_id": action.action_id,
                            "status": (
                                "permission_required"
                            ),
                            "error": permission_reason,
                        }
                    )

                    progress_made = True

                    continue

                task.current_action = (
                    action.action_id
                )

                action.status = "running"
                action.started_at = time.time()
                action.attempts += 1

                logger.info(
                    "Falcon worker executing action %s.",
                    action.action_id,
                )

                try:

                    result = self._execute_action(
                        task,
                        action,
                    )

                    action.result = result

                    verified, verification_reason = (
                        self._verify_action(
                            task,
                            action,
                            result,
                        )
                    )

                    if not verified:

                        action.status = "failed"

                        action.error = (
                            verification_reason
                            or "Action verification failed."
                        )

                        task.errors.append(
                            {
                                "action_id": action.action_id,
                                "error": action.error,
                            }
                        )

                        progress_made = True

                        if self._recover_action(
                            task,
                            action,
                        ):

                            continue

                        continue

                    action.status = "complete"
                    action.finished_at = time.time()

                    task.results.append(
                        {
                            "action_id": action.action_id,
                            "name": action.name,
                            "type": action.action_type,
                            "tool": action.tool,
                            "agent": action.agent,
                            "status": "complete",
                            "result": result,
                            "attempts": action.attempts,
                        }
                    )

                    progress_made = True

                except Exception as exc:

                    logger.exception(
                        "Falcon worker action failed: %s",
                        action.action_id,
                    )

                    action.status = "failed"
                    action.error = str(exc)
                    action.finished_at = time.time()

                    task.errors.append(
                        {
                            "action_id": action.action_id,
                            "error": str(exc),
                            "attempts": action.attempts,
                        }
                    )

                    progress_made = True

                    if self._recover_action(
                        task,
                        action,
                    ):

                        continue

            if task.status == "cancelled":

                break

            if not progress_made:

                task.status = "failed"

                task.errors.append(
                    {
                        "error": (
                            "Worker could not make further "
                            "progress because unresolved "
                            "dependencies remain."
                        )
                    }
                )

                break

        task.current_action = None
        task.finished_at = time.time()

        if task.status != "cancelled":

            failed = any(
                action.status == "failed"
                for action in task.actions
            )

            permission_required = any(
                action.status
                == "permission_required"
                for action in task.actions
            )

            incomplete = any(
                action.status
                not in {
                    "complete",
                }
                for action in task.actions
            )

            if permission_required:

                task.status = "permission_required"

            elif failed:

                task.status = "failed"

            elif incomplete:

                task.status = "incomplete"

            else:

                task.status = "complete"

        logger.info(
            "Falcon worker task %s finished with status=%s.",
            task_id,
            task.status,
        )

        return self.snapshot(
            task_id
        )

    # ========================================================
    # CANCELLATION
    # ========================================================

    def cancel_task(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """
        Cancel a running or pending task.
        """

        task = self.tasks.get(
            task_id
        )

        if task is None:

            return {
                "status": "error",
                "error": "Worker task not found.",
            }

        if task.status in {
            "complete",
            "failed",
        }:

            return self.snapshot(
                task_id
            )

        task.status = "cancelled"
        task.finished_at = time.time()

        if task.current_action:

            for action in task.actions:

                if (
                    action.action_id
                    == task.current_action
                    and action.status == "running"
                ):

                    action.status = "cancelled"

        logger.info(
            "Falcon worker task cancelled: %s",
            task_id,
        )

        return self.snapshot(
            task_id
        )

    # ========================================================
    # RESUME
    # ========================================================

    def resume_task(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """
        Resume a task that stopped before completion.
        """

        task = self.tasks.get(
            task_id
        )

        if task is None:

            return {
                "status": "error",
                "error": "Worker task not found.",
            }

        if task.status == "complete":

            return self.snapshot(
                task_id
            )

        if task.status == "cancelled":

            task.status = "pending"

        elif task.status in {
            "failed",
            "incomplete",
            "permission_required",
        }:

            task.status = "pending"

        for action in task.actions:

            if action.status in {
                "running",
                "permission_required",
            }:

                action.status = "pending"

        return self.run_task(
            task_id
        )

    # ========================================================
    # PROGRESS
    # ========================================================

    def progress(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """
        Return lightweight task progress.
        """

        task = self.tasks.get(
            task_id
        )

        if task is None:

            return {
                "status": "error",
                "error": "Worker task not found.",
            }

        total = len(
            task.actions
        )

        completed = sum(
            1
            for action in task.actions
            if action.status == "complete"
        )

        failed = sum(
            1
            for action in task.actions
            if action.status == "failed"
        )

        return {
            "task_id": task.task_id,
            "status": task.status,
            "current_action": task.current_action,
            "total_actions": total,
            "completed_actions": completed,
            "failed_actions": failed,
            "progress": (
                completed / total
                if total
                else 0.0
            ),
        }

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(
        self,
        task_id: str,
    ) -> dict[str, Any]:
        """
        Serialize worker state into a safe dictionary.
        """

        task = self.tasks.get(
            task_id
        )

        if task is None:

            return {
                "status": "error",
                "error": "Worker task not found.",
            }

        return {
            "task_id": task.task_id,
            "username": task.username,
            "question": task.question,
            "status": task.status,
            "current_action": task.current_action,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "finished_at": task.finished_at,
            "metadata": dict(
                task.metadata
            ),
            "actions": [
                {
                    "action_id": action.action_id,
                    "name": action.name,
                    "action_type": action.action_type,
                    "tool": action.tool,
                    "agent": action.agent,
                    "input": action.input,
                    "depends_on": list(
                        action.depends_on
                    ),
                    "requires_permission": (
                        action.requires_permission
                    ),
                    "status": action.status,
                    "result": action.result,
                    "error": action.error,
                    "attempts": action.attempts,
                    "started_at": action.started_at,
                    "finished_at": action.finished_at,
                }
                for action in task.actions
            ],
            "results": list(
                task.results
            ),
            "errors": list(
                task.errors
            ),
        }


# ============================================================
# FACTORY
# ============================================================

def create_worker(
    *,
    tool_executor: Callable[..., Any] | None = None,
    agent_executor: Callable[..., Any] | None = None,
    permission_checker: Callable[..., Any] | None = None,
    verifier: Callable[..., Any] | None = None,
) -> WorkerEngine:
    """
    Create a configured Falcon Worker Engine.
    """

    return WorkerEngine(
        tool_executor=tool_executor,
        agent_executor=agent_executor,
        permission_checker=permission_checker,
        verifier=verifier,
    )
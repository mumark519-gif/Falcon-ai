from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from app.core.logger import logger


VALID_STEP_TYPES = {
    "agent",
    "tool",
}

VALID_STATUSES = {
    "pending",
    "ready",
    "running",
    "completed",
    "failed",
    "skipped",
}

TERMINAL_STATUSES = {
    "completed",
    "failed",
    "skipped",
}


# ============================================================
# HELPERS
# ============================================================

def _utc_now() -> str:
    """
    Return a consistent UTC timestamp for workflow events.
    """

    return datetime.utcnow().isoformat()


def _normalize_dependencies(
    dependencies: Any,
) -> list[str]:
    """
    Normalize dependency declarations into a list of step IDs.
    """

    if dependencies is None:
        return []

    if isinstance(dependencies, str):
        dependencies = [dependencies]

    if not isinstance(dependencies, list):
        return []

    normalized = []

    for dependency in dependencies:

        if dependency is None:
            continue

        dependency_id = str(
            dependency
        ).strip()

        if not dependency_id:
            continue

        if dependency_id not in normalized:
            normalized.append(
                dependency_id
            )

    return normalized


def _normalize_step(
    step: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    """
    Normalize one planner step into Falcon's workflow contract.
    """

    normalized = deepcopy(step)

    step_id = str(
        normalized.get(
            "id",
            f"step_{index + 1}",
        )
    ).strip()

    if not step_id:
        step_id = f"step_{index + 1}"

    step_type = str(
        normalized.get(
            "type",
            "agent",
        )
    ).strip().lower()

    status = str(
        normalized.get(
            "status",
            "pending",
        )
    ).strip().lower()

    if status not in VALID_STATUSES:
        status = "pending"

    try:
        attempts = int(
            normalized.get(
                "attempts",
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        attempts = 0

    normalized["id"] = step_id
    normalized["type"] = step_type
    normalized["status"] = status
    normalized["attempts"] = max(
        0,
        attempts,
    )

    normalized["dependencies"] = (
        _normalize_dependencies(
            normalized.get(
                "dependencies",
                [],
            )
        )
    )

    normalized["error"] = normalized.get(
        "error"
    )

    normalized["created_at"] = (
        normalized.get(
            "created_at"
        )
        or _utc_now()
    )

    normalized["started_at"] = (
        normalized.get(
            "started_at"
        )
    )

    normalized["completed_at"] = (
        normalized.get(
            "completed_at"
        )
    )

    normalized["updated_at"] = (
        normalized.get(
            "updated_at"
        )
        or _utc_now()
    )

    return normalized


# ============================================================
# WORKFLOW VALIDATION
# ============================================================

def _validate_unique_ids(
    workflow: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Ensure every workflow step has a unique ID.
    """

    seen: set[str] = set()

    for index, step in enumerate(workflow):

        step_id = step.get(
            "id",
            f"step_{index + 1}",
        )

        if step_id not in seen:

            seen.add(step_id)
            continue

        original_id = step_id
        counter = 2

        while step_id in seen:

            step_id = (
                f"{original_id}_{counter}"
            )

            counter += 1

        step["id"] = step_id

        logger.warning(
            "Duplicate workflow step ID '%s'. "
            "Renamed to '%s'.",
            original_id,
            step_id,
        )

        seen.add(step_id)

    return workflow


def _validate_dependencies(
    workflow: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Validate that dependency references point to real steps.
    """

    step_ids = {
        step.get("id")
        for step in workflow
    }

    for step in workflow:

        dependencies = step.get(
            "dependencies",
            [],
        )

        invalid_dependencies = [
            dependency
            for dependency in dependencies
            if dependency not in step_ids
        ]

        if invalid_dependencies:

            step["status"] = "failed"

            step["error"] = (
                "Unknown workflow dependency: "
                + ", ".join(
                    invalid_dependencies
                )
            )

            logger.error(
                "Workflow step '%s' has invalid "
                "dependencies: %s",
                step.get("id"),
                invalid_dependencies,
            )

    return workflow


def _validate_dependency_cycles(
    workflow: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Detect dependency cycles.

    A cycle would otherwise prevent the workflow from ever
    becoming executable.
    """

    dependencies = {
        step["id"]: set(
            step.get(
                "dependencies",
                [],
            )
        )
        for step in workflow
        if step.get("id")
    }

    visiting: set[str] = set()
    visited: set[str] = set()

    cyclic_steps: set[str] = set()

    def visit(
        step_id: str,
        path: list[str],
    ) -> None:

        if step_id in visiting:

            if step_id in path:

                cycle_start = path.index(
                    step_id
                )

                cyclic_steps.update(
                    path[cycle_start:]
                )

            return

        if step_id in visited:
            return

        visiting.add(step_id)

        path.append(
            step_id
        )

        for dependency in dependencies.get(
            step_id,
            set(),
        ):

            if dependency in dependencies:

                visit(
                    dependency,
                    path,
                )

        path.pop()

        visiting.remove(
            step_id
        )

        visited.add(
            step_id
        )

    for step_id in dependencies:

        visit(
            step_id,
            [],
        )

    for step in workflow:

        if step["id"] in cyclic_steps:

            step["status"] = "failed"

            step["error"] = (
                "Workflow dependency cycle detected."
            )

            logger.error(
                "Dependency cycle detected involving "
                "workflow step '%s'.",
                step["id"],
            )

    return workflow


# ============================================================
# WORKFLOW PREPARATION
# ============================================================

def execute_workflow(
    plan: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Prepare a planner output for execution.

    This function DOES NOT execute tools or agents.

    It creates Falcon's explicit workflow state.

    Actual execution remains in execution_engine.py.
    """

    logger.info(
        "Preparing Falcon workflow..."
    )

    if not isinstance(
        plan,
        dict,
    ):
        logger.warning(
            "Workflow plan is not a dictionary."
        )

        return []

    raw_steps = plan.get(
        "steps",
        [],
    )

    if not isinstance(
        raw_steps,
        list,
    ):
        logger.warning(
            "Workflow plan contains invalid steps."
        )

        return []

    workflow: list[
        dict[str, Any]
    ] = []

    for index, step in enumerate(
        raw_steps
    ):

        if not isinstance(
            step,
            dict,
        ):

            workflow.append(
                {
                    "id": f"step_{index + 1}",
                    "type": "unknown",
                    "status": "failed",
                    "attempts": 0,
                    "dependencies": [],
                    "error": (
                        "Invalid workflow step."
                    ),
                    "step": step,
                    "created_at": _utc_now(),
                    "started_at": None,
                    "completed_at": None,
                    "updated_at": _utc_now(),
                }
            )

            continue

        normalized = _normalize_step(
            step,
            index,
        )

        if normalized["type"] not in VALID_STEP_TYPES:

            normalized["status"] = "failed"

            normalized["error"] = (
                "Unsupported step type: "
                + normalized["type"]
            )

        workflow.append(
            normalized
        )

    workflow = _validate_unique_ids(
        workflow
    )

    workflow = _validate_dependencies(
        workflow
    )

    workflow = _validate_dependency_cycles(
        workflow
    )

    refresh_ready_steps(
        workflow
    )

    logger.info(
        "Falcon workflow prepared with %s steps.",
        len(workflow),
    )

    return workflow


# ============================================================
# DEPENDENCY MANAGEMENT
# ============================================================

def dependencies_completed(
    workflow: list[dict[str, Any]],
    step: dict[str, Any],
) -> bool:
    """
    Return True when every dependency of a step completed.
    """

    dependencies = step.get(
        "dependencies",
        [],
    )

    if not dependencies:
        return True

    steps_by_id = {
        item.get("id"): item
        for item in workflow
    }

    for dependency_id in dependencies:

        dependency = steps_by_id.get(
            dependency_id
        )

        if dependency is None:
            return False

        if dependency.get(
            "status"
        ) != "completed":

            return False

    return True


def has_failed_dependency(
    workflow: list[dict[str, Any]],
    step: dict[str, Any],
) -> bool:
    """
    Return True when one of a step's dependencies failed
    or was skipped.
    """

    dependencies = step.get(
        "dependencies",
        [],
    )

    if not dependencies:
        return False

    steps_by_id = {
        item.get("id"): item
        for item in workflow
    }

    for dependency_id in dependencies:

        dependency = steps_by_id.get(
            dependency_id
        )

        if dependency is None:
            return True

        if dependency.get(
            "status"
        ) in {
            "failed",
            "skipped",
        }:

            return True

    return False


def get_ready_steps(
    workflow: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Return steps that are ready for the execution engine.
    """

    ready = []

    for step in workflow:

        if step.get(
            "status"
        ) not in {
            "pending",
            "ready",
        }:

            continue

        if has_failed_dependency(
            workflow,
            step,
        ):

            continue

        if dependencies_completed(
            workflow,
            step,
        ):

            ready.append(
                step
            )

    return ready


def refresh_ready_steps(
    workflow: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Update pending steps whose dependencies are complete.
    """

    ready_steps = get_ready_steps(
        workflow
    )

    ready_ids = {
        step["id"]
        for step in ready_steps
    }

    for step in workflow:

        if (
            step.get("status")
            == "pending"
            and step.get("id")
            in ready_ids
        ):

            step["status"] = "ready"
            step["updated_at"] = _utc_now()

    return workflow


# ============================================================
# STEP LIFECYCLE
# ============================================================

def mark_step_running(
    workflow: list[dict[str, Any]],
    step_id: str,
):
    """
    Mark a workflow step as running.
    """

    for step in workflow:

        if step.get("id") != step_id:
            continue

        if step.get(
            "status"
        ) in TERMINAL_STATUSES:

            logger.warning(
                "Cannot run terminal workflow step '%s'.",
                step_id,
            )

            return step

        step["status"] = "running"

        step["attempts"] = (
            int(
                step.get(
                    "attempts",
                    0,
                )
            )
            + 1
        )

        step["started_at"] = (
            step.get(
                "started_at"
            )
            or _utc_now()
        )

        step["updated_at"] = _utc_now()

        return step

    return None


def mark_step_completed(
    workflow: list[dict[str, Any]],
    step_id: str,
    result: Any = None,
):
    """
    Mark a workflow step as successfully completed.
    """

    for step in workflow:

        if step.get("id") != step_id:
            continue

        step["status"] = "completed"

        step["error"] = None

        step["completed_at"] = _utc_now()

        step["updated_at"] = _utc_now()

        if result is not None:

            step["result"] = result

        return step

    return None


def mark_step_failed(
    workflow: list[dict[str, Any]],
    step_id: str,
    error: str,
):
    """
    Mark a workflow step as failed.
    """

    for step in workflow:

        if step.get("id") != step_id:
            continue

        step["status"] = "failed"

        step["error"] = (
            str(error)
            if error
            else "Workflow step failed."
        )

        step["completed_at"] = _utc_now()

        step["updated_at"] = _utc_now()

        return step

    return None


def mark_step_skipped(
    workflow: list[dict[str, Any]],
    step_id: str,
    reason: str = "Step skipped.",
):
    """
    Mark a workflow step as skipped.
    """

    for step in workflow:

        if step.get("id") != step_id:
            continue

        step["status"] = "skipped"

        step["error"] = reason

        step["completed_at"] = _utc_now()

        step["updated_at"] = _utc_now()

        return step

    return None


# ============================================================
# WORKFLOW STATE
# ============================================================

def get_step(
    workflow: list[dict[str, Any]],
    step_id: str,
):
    """
    Retrieve a workflow step by ID.
    """

    for step in workflow:

        if step.get("id") == step_id:
            return step

    return None


def all_steps_terminal(
    workflow: list[dict[str, Any]],
) -> bool:
    """
    Determine whether the workflow has finished.
    """

    if not workflow:
        return False

    return all(
        step.get("status")
        in TERMINAL_STATUSES
        for step in workflow
    )


def workflow_failed(
    workflow: list[dict[str, Any]],
) -> bool:
    """
    Determine whether the workflow contains a failure.
    """

    return any(
        step.get("status")
        == "failed"
        for step in workflow
    )


def workflow_completed(
    workflow: list[dict[str, Any]],
) -> bool:
    """
    Determine whether every workflow step completed successfully.
    """

    if not workflow:
        return False

    return all(
        step.get("status")
        == "completed"
        for step in workflow
    )


# ============================================================
# SUMMARY
# ============================================================

def workflow_summary(
    workflow: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Produce a complete workflow execution summary.
    """

    total = len(
        workflow
    )

    completed = sum(
        1
        for step in workflow
        if step.get(
            "status"
        ) == "completed"
    )

    failed = sum(
        1
        for step in workflow
        if step.get(
            "status"
        ) == "failed"
    )

    running = sum(
        1
        for step in workflow
        if step.get(
            "status"
        ) == "running"
    )

    pending = sum(
        1
        for step in workflow
        if step.get(
            "status"
        ) == "pending"
    )

    ready = sum(
        1
        for step in workflow
        if step.get(
            "status"
        ) == "ready"
    )

    skipped = sum(
        1
        for step in workflow
        if step.get(
            "status"
        ) == "skipped"
    )

    terminal = sum(
        1
        for step in workflow
        if step.get(
            "status"
        ) in TERMINAL_STATUSES
    )

    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "running": running,
        "pending": pending,
        "ready": ready,
        "skipped": skipped,
        "terminal": terminal,
        "finished": (
            total > 0
            and terminal == total
        ),
        "success": (
            total > 0
            and completed == total
        ),
        "failed_workflow": (
            failed > 0
        ),
    }
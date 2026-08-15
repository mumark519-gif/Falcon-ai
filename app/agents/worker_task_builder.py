from __future__ import annotations

import json
import uuid
from typing import Any

from app.ai_service import ask_ai
from app.core.logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

MAX_ACTIONS = 50


# ============================================================
# PROMPT
# ============================================================

WORKER_TASK_PROMPT = """
You are Falcon AI's General Worker Task Builder.

Your job is to convert a user's goal or an existing execution
plan into a concrete sequence of executable actions.

Falcon is a general-purpose AI system.

Actions may eventually involve:

- specialist agents
- web search
- document search
- Python
- browser
- GitHub
- files
- APIs
- plugins
- image generation
- image analysis
- video
- audio
- voice
- enterprise systems
- external services
- autonomous computer actions

You must NOT assume that every capability is currently
available.

The worker task must describe WHAT needs to happen, not pretend
that an unavailable tool already exists.

Rules:

1. Break complex goals into clear atomic actions.

2. Keep actions ordered logically.

3. Represent dependencies explicitly.

4. Do not create unnecessary actions.

5. Do not execute anything.

6. Do not claim that any tool has already run.

7. Do not invent information.

8. Use the smallest reasonable number of actions.

9. An action should have a clear objective and concrete input.

10. Actions that require a previous result must use depends_on.

11. Actions that change external state should normally require
    permission.

12. Reading information normally does not require permission.

13. High-risk or irreversible actions should require permission.

14. Prefer existing Falcon capabilities when they clearly fit.

15. Do not create a browser action simply because a website was
    mentioned.

16. Do not create a Python action merely because numbers appear.

17. If the task cannot yet be completed because information is
    missing, represent the missing-information requirement.

18. Keep the plan generic enough that future Falcon tools can
    execute it.

Return ONLY valid JSON.

Format:

{
    "task_id": "generated-id",
    "goal": "...",
    "actions": [
        {
            "action_id": "action_1",
            "name": "...",
            "action_type": "tool|agent|function",
            "tool": null,
            "agent": null,
            "input": "...",
            "depends_on": [],
            "requires_permission": false
        }
    ],
    "missing_information": [],
    "risks": [],
    "confidence": 0.0
}
"""


# ============================================================
# JSON PARSING
# ============================================================

def _parse_json(
    response: str,
) -> dict[str, Any]:
    """
    Safely parse model output into a dictionary.
    """

    text = str(
        response or ""
    ).strip()

    if text.startswith(
        "```"
    ):

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

    try:

        result = json.loads(
            text
        )

        if isinstance(
            result,
            dict,
        ):

            return result

    except Exception:

        pass

    return {
        "task_id": str(
            uuid.uuid4()
        ),
        "goal": "",
        "actions": [],
        "missing_information": [
            "Worker task builder returned invalid JSON."
        ],
        "risks": [],
        "confidence": 0.0,
    }


# ============================================================
# ACTION NORMALIZATION
# ============================================================

def _normalize_action(
    action: Any,
    index: int,
) -> dict[str, Any]:
    """
    Normalize one worker action.
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
            "description"
        )
        or action.get(
            "task"
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
        or "function"
    ).strip().lower()

    if action_type not in {
        "tool",
        "agent",
        "function",
    }:

        action_type = "function"

    tool = action.get(
        "tool"
    )

    if tool:

        tool = str(
            tool
        ).strip().lower()

    else:

        tool = None

    agent = action.get(
        "agent"
    )

    if agent:

        agent = str(
            agent
        ).strip().upper()

    else:

        agent = None

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

    dependencies = []

    for dependency in depends_on:

        dependency = str(
            dependency
        ).strip()

        if dependency:

            dependencies.append(
                dependency
            )

    return {
        "action_id": action_id,
        "name": name,
        "action_type": action_type,
        "tool": tool,
        "agent": agent,
        "input": action.get(
            "input",
            action.get(
                "task",
                "",
            ),
        ),
        "depends_on": dependencies,
        "requires_permission": bool(
            action.get(
                "requires_permission",
                False,
            )
        ),
    }


# ============================================================
# TASK NORMALIZATION
# ============================================================

def _normalize_task(
    task: dict[str, Any],
    question: str,
) -> dict[str, Any]:
    """
    Normalize the complete worker task.
    """

    actions = task.get(
        "actions",
        [],
    )

    if not isinstance(
        actions,
        list,
    ):

        actions = []

    actions = [
        _normalize_action(
            action,
            index,
        )
        for index, action in enumerate(
            actions[
                :MAX_ACTIONS
            ],
            start=1,
        )
    ]

    goal = str(
        task.get(
            "goal",
            question,
        )
        or question
    ).strip()

    missing_information = task.get(
        "missing_information",
        [],
    )

    if not isinstance(
        missing_information,
        list,
    ):

        missing_information = [
            missing_information
        ]

    risks = task.get(
        "risks",
        [],
    )

    if not isinstance(
        risks,
        list,
    ):

        risks = [
            risks
        ]

    try:

        confidence = float(
            task.get(
                "confidence",
                0.5,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        confidence = 0.5

    confidence = max(
        0.0,
        min(
            1.0,
            confidence,
        ),
    )

    return {
        "task_id": str(
            task.get(
                "task_id"
            )
            or uuid.uuid4()
        ),
        "goal": goal,
        "actions": actions,
        "missing_information": [
            str(item)
            for item in missing_information
            if str(item).strip()
        ],
        "risks": [
            str(item)
            for item in risks
            if str(item).strip()
        ],
        "confidence": confidence,
    }


# ============================================================
# DEPENDENCY VALIDATION
# ============================================================

def _validate_dependencies(
    actions: list[dict[str, Any]],
) -> list[str]:
    """
    Detect invalid or circular action dependencies.
    """

    action_ids = {
        action.get(
            "action_id"
        )
        for action in actions
    }

    errors = []

    for action in actions:

        action_id = action.get(
            "action_id"
        )

        dependencies = action.get(
            "depends_on",
            [],
        )

        for dependency in dependencies:

            if dependency not in action_ids:

                errors.append(
                    (
                        f"Action '{action_id}' "
                        f"depends on missing action "
                        f"'{dependency}'."
                    )
                )

            if dependency == action_id:

                errors.append(
                    (
                        f"Action '{action_id}' "
                        "depends on itself."
                    )
                )

    # Basic cycle detection.

    graph = {
        action.get(
            "action_id"
        ): action.get(
            "depends_on",
            [],
        )
        for action in actions
    }

    def visit(
        node: str,
        path: set[str],
    ) -> None:

        if node in path:

            errors.append(
                f"Circular dependency detected at '{node}'."
            )

            return

        dependencies = graph.get(
            node,
            [],
        )

        new_path = set(
            path
        )

        new_path.add(
            node
        )

        for dependency in dependencies:

            if dependency in graph:

                visit(
                    dependency,
                    new_path,
                )

    for action_id in graph:

        visit(
            action_id,
            set(),
        )

    return list(
        dict.fromkeys(
            errors
        )
    )


# ============================================================
# BUILD TASK
# ============================================================

def build_worker_task(
    *,
    question: str,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a structured worker task.

    If an existing Falcon plan is supplied, the model uses it as
    the primary planning context instead of starting from zero.
    """

    question = str(
        question or ""
    ).strip()

    if not question:

        return {
            "task_id": str(
                uuid.uuid4()
            ),
            "goal": "",
            "actions": [],
            "missing_information": [
                "No user request was supplied."
            ],
            "risks": [],
            "confidence": 0.0,
        }

    plan = (
        plan
        if isinstance(
            plan,
            dict,
        )
        else {}
    )

    prompt = (
        WORKER_TASK_PROMPT
        + "\n\nUSER GOAL:\n"
        + question
        + "\n\nEXISTING FALCON PLAN:\n"
        + json.dumps(
            plan,
            ensure_ascii=False,
            default=str,
        )
    )

    try:

        response = ask_ai(
            prompt
        )

        task = _parse_json(
            response
        )

        task = _normalize_task(
            task,
            question,
        )

        dependency_errors = (
            _validate_dependencies(
                task.get(
                    "actions",
                    [],
                )
            )
        )

        if dependency_errors:

            task.setdefault(
                "risks",
                [],
            )

            task["risks"].extend(
                dependency_errors
            )

            task["confidence"] = min(
                float(
                    task.get(
                        "confidence",
                        0.5,
                    )
                ),
                0.3,
            )

        logger.info(
            "Falcon worker task built: %s actions.",
            len(
                task.get(
                    "actions",
                    [],
                )
            ),
        )

        return task

    except Exception as exc:

        logger.exception(
            "Worker task construction failed."
        )

        return {
            "task_id": str(
                uuid.uuid4()
            ),
            "goal": question,
            "actions": [],
            "missing_information": [],
            "risks": [
                f"Worker task construction failed: {exc}"
            ],
            "confidence": 0.0,
        }


# ============================================================
# PLAN → WORKER TASK
# ============================================================

def build_worker_task_from_plan(
    *,
    question: str,
    plan: dict[str, Any],
) -> dict[str, Any]:
    """
    Explicit helper for converting Falcon's planner output
    into worker-ready task state.
    """

    return build_worker_task(
        question=question,
        plan=plan,
    )
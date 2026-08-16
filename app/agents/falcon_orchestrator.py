from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Callable

from app.core.logger import logger

from app.intelligence.reasoning import ReasoningController
from app.intelligence.planning import planner
from app.intelligence.model_router import model_router
from app.intelligence.reflection import ReflectionController
from app.intelligence.execution import ExecutionController


class FalconOrchestrator:
    """
    Top-level cognitive control plane for Falcon AI.

    This component is intentionally kept separate from the existing
    app.agents.orchestrator.py.

    Responsibilities:
        1. Understand the user's goal.
        2. Build a reasoning trace.
        3. Create an execution plan.
        4. Select an available model.
        5. Coordinate optional execution.
        6. Verify execution/output state.
        7. Reflect on the result.
        8. Produce the final response.

    It does NOT fabricate completed actions.

    Long-term role:
        This is the control plane that can eventually sit above
        Falcon's own intelligence/model.
    """

    def __init__(self) -> None:
        self.reasoning = ReasoningController()
        self.reflection = ReflectionController()
        self.execution = ExecutionController()

    # ============================================================
    # SERIALIZATION HELPERS
    # ============================================================

    @staticmethod
    def _serialize(value: Any) -> Any:
        """
        Convert dataclasses and common objects into safe dictionaries.

        The internal intelligence objects should not be returned directly
        through the API because they may not be JSON serializable.
        """

        if value is None:
            return None

        if is_dataclass(value) and not isinstance(value, type):
            return asdict(value)

        if isinstance(value, dict):
            return {
                str(key): FalconOrchestrator._serialize(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                FalconOrchestrator._serialize(item)
                for item in value
            ]

        if isinstance(value, (str, int, float, bool)):
            return value

        if hasattr(value, "__dict__"):
            try:
                return {
                    str(key): FalconOrchestrator._serialize(item)
                    for key, item in vars(value).items()
                }
            except Exception:
                pass

        return str(value)

    @staticmethod
    def _safe_context(
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not isinstance(context, dict):
            return {}

        return dict(context)

    # ============================================================
    # PREPARATION
    # ============================================================

    def prepare(
        self,
        goal: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Prepare Falcon's cognitive state without executing the goal.
        """

        goal = str(goal or "").strip()

        if not goal:
            raise ValueError(
                "Falcon requires a non-empty goal."
            )

        context = self._safe_context(context)

        logger.info(
            "Falcon Intelligence preparing goal."
        )

        # --------------------------------------------------------
        # Reasoning trace
        # --------------------------------------------------------

        trace = self.reasoning.build(goal)

        # --------------------------------------------------------
        # Execution plan
        # --------------------------------------------------------

        plan = planner.create(goal)

        # --------------------------------------------------------
        # Model selection
        # --------------------------------------------------------

        decision = model_router.choose(goal)

        state = {
            "goal": goal,
            "context": context,
            "trace": self._serialize(trace),
            "plan": self._serialize(plan),
            "model": self._serialize(decision),
            "status": "prepared",
        }

        logger.info(
            "Falcon Intelligence preparation completed."
        )

        return state

    # ============================================================
    # EXECUTION
    # ============================================================

    def execute(
        self,
        fn: Callable[[], Any],
        retries: int = 2,
    ) -> dict[str, Any]:
        """
        Execute an approved operation through Falcon's execution
        controller.

        This is intentionally generic so higher-level systems can
        provide the actual operation.
        """

        result = self.execution.run(
            fn,
            retries=retries,
        )

        serialized = self._serialize(result)

        if isinstance(serialized, dict):
            return serialized

        return {
            "success": False,
            "output": None,
            "error": "Invalid execution result.",
            "attempts": retries + 1,
        }

    # ============================================================
    # VERIFICATION
    # ============================================================

    def verify(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Verify the execution state without claiming that an action
        succeeded merely because an output exists.
        """

        if not isinstance(result, dict):
            return {
                "passed": False,
                "issues": [
                    "Execution result is not a dictionary."
                ],
                "retry_recommended": True,
            }

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        error = result.get("error")

        if error:
            return {
                "passed": False,
                "issues": [str(error)],
                "retry_recommended": True,
            }

        if not success:
            return {
                "passed": False,
                "issues": [
                    "Execution was not confirmed successful."
                ],
                "retry_recommended": True,
            }

        return {
            "passed": True,
            "issues": [],
            "retry_recommended": False,
        }

    # ============================================================
    # RESPONSE GENERATION
    # ============================================================

    def _generate_response(
        self,
        goal: str,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """
        Generate a user-facing response through the existing model
        router.

        The model router remains the provider abstraction for now.
        Falcon's own model can later replace this layer without
        changing the control plane.
        """

        response = model_router.generate(
            goal,
            prompt,
            **kwargs,
        )

        return str(
            response or ""
        ).strip()

    # ============================================================
    # MAIN INTELLIGENCE FLOW
    # ============================================================

    def answer(
        self,
        goal: str,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Run Falcon's complete top-level intelligence cycle.

        Flow:

            Goal
              ↓
            Prepare
              ↓
            Reason
              ↓
            Plan
              ↓
            Optional execution
              ↓
            Verify
              ↓
            Generate response
              ↓
            Reflect
              ↓
            Return state

        If an execution function is supplied through kwargs:

            execute_fn=callable

        it will be executed through ExecutionController.

        Otherwise Falcon performs a reasoning/response cycle without
        pretending that an external action was completed.
        """

        goal = str(goal or "").strip()

        if not goal:
            return {
                "status": "error",
                "goal": "",
                "response": (
                    "Please provide a question or task."
                ),
                "error": "empty_goal",
            }

        context = self._safe_context(
            context
        )

        execute_fn = kwargs.pop(
            "execute_fn",
            None,
        )

        retries = kwargs.pop(
            "retries",
            2,
        )

        prompt = kwargs.pop(
            "prompt",
            goal,
        )

        try:
            # ====================================================
            # 1. PREPARE
            # ====================================================

            state = self.prepare(
                goal=goal,
                context=context,
            )

            # ====================================================
            # 2. REASONING
            # ====================================================

            trace = self.reasoning.build(
                goal
            )

            state["trace"] = self._serialize(
                trace
            )

            next_step = self.reasoning.next_step(
                trace
            )

            if next_step is not None:
                self.reasoning.mark(
                    trace,
                    next_step.name,
                    status="complete",
                )

            # ====================================================
            # 3. OPTIONAL EXECUTION
            # ====================================================

            execution_result: dict[str, Any] = {
                "success": False,
                "executed": False,
                "output": None,
                "error": None,
                "attempts": 0,
            }

            if callable(execute_fn):
                execution_result = self.execute(
                    execute_fn,
                    retries=retries,
                )

                execution_result["executed"] = True

            state["execution"] = execution_result

            # ====================================================
            # 4. VERIFICATION
            # ====================================================

            if execution_result.get(
                "executed",
                False,
            ):
                verification = self.verify(
                    execution_result
                )
            else:
                verification = {
                    "passed": True,
                    "issues": [],
                    "retry_recommended": False,
                    "execution_performed": False,
                }

            state["verification"] = verification

            # ====================================================
            # 5. BUILD FINAL PROMPT
            # ====================================================

            final_prompt = (
                str(prompt)
                + "\n\n"
                + "FALCON INTERNAL EXECUTION STATE:\n"
                + str(
                    self._serialize(
                        {
                            "plan": state.get(
                                "plan",
                                {},
                            ),
                            "execution": execution_result,
                            "verification": verification,
                            "context": context,
                        }
                    )
                )
                + "\n\n"
                + (
                    "Answer the user's request directly. "
                    "Do not claim an external action was completed "
                    "unless execution was actually successful and "
                    "verified."
                )
            )

            # ====================================================
            # 6. GENERATE RESPONSE
            # ====================================================

            response = self._generate_response(
                goal,
                final_prompt,
                **kwargs,
            )

            if not response:
                response = (
                    "Falcon completed its processing but "
                    "did not produce a usable response."
                )

            state["response"] = response

            # ====================================================
            # 7. REFLECTION
            # ====================================================

            reflection_input = {
                "status": "complete",
                "executed": execution_result.get(
                    "executed",
                    False,
                ),
                "success": execution_result.get(
                    "success",
                    False,
                ),
                "error": execution_result.get(
                    "error"
                ),
                "response_generated": bool(
                    response
                ),
                "verified": verification.get(
                    "passed",
                    False,
                ),
            }

            reflection = self.reflection.inspect(
                reflection_input
            )

            state["reflection"] = self._serialize(
                reflection
            )

            # ====================================================
            # 8. FINAL STATUS
            # ====================================================

            if reflection.get(
                "passed",
                False,
            ):
                state["status"] = "complete"
            else:
                state["status"] = "completed_with_warnings"

            logger.info(
                "Falcon Intelligence answer completed: status=%s",
                state["status"],
            )

            return self._serialize(
                state
            )

        except Exception as exc:
            logger.exception(
                "Falcon Intelligence orchestration failed."
            )

            return {
                "status": "error",
                "goal": goal,
                "context": context,
                "response": (
                    "Falcon encountered an internal processing "
                    "error while handling your request."
                ),
                "error": str(exc),
            }


# ============================================================
# SINGLE SHARED ORCHESTRATOR INSTANCE
# ============================================================

orchestrator = FalconOrchestrator()
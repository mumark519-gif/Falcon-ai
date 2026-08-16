from __future__ import annotations

import uuid
from typing import Any

from app.ai_service import ask_ai
from app.agents.execution_engine import execute_plan
from app.agents.planner import create_plan
from app.agents.reflection_engine import reflect
from app.agents.verification_engine import verify_execution


class FalconIntelligence:
    """
    Unified Falcon cognition loop.

    Pipeline:

        understand
            -> plan
            -> execute
            -> summarize
            -> reflect
            -> verify
            -> synthesize

    This class coordinates Falcon's existing intelligence,
    planning, execution, reflection, verification, and AI
    generation layers.

    It does not directly execute tools itself.
    """

    def __init__(
        self,
        tool_manager=None,
    ) -> None:
        self.tool_manager = tool_manager

    # ========================================================
    # UNDERSTANDING
    # ========================================================

    def understand(
        self,
        goal: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Normalize the user's goal and create a task state.
        """

        normalized_goal = str(
            goal or ""
        ).strip()

        return {
            "goal": normalized_goal,
            "context": (
                dict(context)
                if isinstance(context, dict)
                else {}
            ),
            "task_id": str(
                uuid.uuid4()
            ),
        }

    # ========================================================
    # PLANNING
    # ========================================================

    def plan(
        self,
        goal: str,
    ) -> Any:
        """
        Create an execution plan using Falcon's planner.
        """

        if not goal.strip():
            raise ValueError(
                "Falcon cannot create a plan for an empty goal."
            )

        return create_plan(
            goal
        )

    # ========================================================
    # EXECUTION
    # ========================================================

    def execute(
        self,
        plan: Any,
        context: dict[str, Any],
        username: str = "falcon",
        question: str = "",
        memories: list | None = None,
        use_web: bool = False,
        use_documents: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a generated Falcon plan.

        The actual work is delegated to the execution engine.
        """

        if not isinstance(
            plan,
            dict,
        ):
            return {
                "status": "error",
                "error": (
                    "Execution plan must be a dictionary."
                ),
                "plan": plan,
                "context": context,
                "completed_steps": 0,
                "failed_steps": 1,
                "total_steps": 0,
            }

        execution_question = (
            question.strip()
            if question
            else str(
                context.get(
                    "goal",
                    "",
                )
            ).strip()
        )

        try:
            result = execute_plan(
                username=username,
                plan=plan,
                question=execution_question,
                use_web=use_web,
                use_documents=use_documents,
                memories=memories or [],
            )

        except Exception as exc:
            return {
                "status": "error",
                "error": (
                    f"Execution failed: {exc}"
                ),
                "plan": plan,
                "context": context,
                "completed_steps": 0,
                "failed_steps": 1,
                "total_steps": 0,
            }

        if not isinstance(
            result,
            dict,
        ):
            return {
                "status": "error",
                "error": (
                    "Execution engine returned "
                    "an invalid result."
                ),
                "plan": plan,
                "context": context,
                "completed_steps": 0,
                "failed_steps": 1,
                "total_steps": 0,
            }

        return result

    # ========================================================
    # DRAFT GENERATION
    # ========================================================

    def create_draft(
        self,
        goal: str,
        execution: dict[str, Any],
    ) -> str:
        """
        Convert the execution state into a factual draft.

        The model is explicitly prohibited from inventing
        successful actions.
        """

        prompt = f"""
Act as Falcon AI's execution-result summarizer.

User Goal:
{goal}

Execution Result:
{execution}

Create a factual draft answer using ONLY information
contained in the execution result.

Rules:

1. Do not invent actions.
2. Do not invent tool results.
3. Do not claim a task completed unless execution supports it.
4. If execution failed, explain the failure.
5. If execution was partial, clearly state that it was partial.
6. Keep the response useful and concise.
"""

        try:
            response = ask_ai(
                prompt
            )

            if response is None:
                return ""

            return str(
                response
            ).strip()

        except Exception:
            return ""

    # ========================================================
    # REFLECTION
    # ========================================================

    def reflect(
        self,
        question: str,
        draft_answer: str,
    ) -> str:
        """
        Review and improve the draft answer.
        """

        draft = str(
            draft_answer or ""
        ).strip()

        if not draft:
            return ""

        try:
            result = reflect(
                question=question,
                draft_answer=draft,
            )

            return str(
                result
            ).strip()

        except Exception:
            return draft

    # ========================================================
    # VERIFICATION
    # ========================================================

    def verify(
        self,
        question: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Deterministically verify execution.
        """

        try:
            verification = verify_execution(
                question=question,
                result=result,
            )

            if isinstance(
                verification,
                dict,
            ):
                return verification

            return {
                "verified": False,
                "reason": (
                    "Verification engine returned "
                    "an invalid result."
                ),
            }

        except Exception as exc:
            return {
                "verified": False,
                "reason": (
                    f"Verification failed: {exc}"
                ),
            }

    # ========================================================
    # SYNTHESIS
    # ========================================================

    def synthesize(
        self,
        goal: str,
        plan: Any,
        execution: dict[str, Any],
        reflection: str,
        verification: dict[str, Any],
    ) -> str:
        """
        Produce the final user-facing Falcon response.

        The synthesis layer must remain grounded in the
        execution and verification state.
        """

        verification_status = bool(
            verification.get(
                "verified",
                False,
            )
        )

        execution_status = str(
            execution.get(
                "status",
                "",
            )
        ).lower()

        prompt = f"""
Act as Falcon AI's final synthesis layer.

User Goal:
{goal}

Plan:
{plan}

Execution State:
{execution}

Reflection:
{reflection}

Verification:
{verification}

Execution Status:
{execution_status}

Verification Passed:
{verification_status}

Produce the best useful final response to the user.

CRITICAL RULES:

1. Never invent tool results.
2. Never invent completed actions.
3. Never claim that an action happened unless the execution
   result supports that claim.
4. Never describe an execution as fully successful when
   verification failed.
5. If execution is partial, clearly say what succeeded and
   what did not.
6. If execution failed, explain the failure honestly.
7. Use the reflection to improve accuracy and clarity.
8. Do not expose internal reasoning or hidden chain-of-thought.
9. Answer the user's actual goal rather than merely
   describing Falcon's internal pipeline.
10. Keep the final answer concise but useful.
"""

        try:
            response = ask_ai(
                prompt
            )

            if response is not None:
                text = str(
                    response
                ).strip()

                if text:
                    return text

        except Exception:
            pass

        # Safe fallback when the synthesis model is unavailable.
        if reflection.strip():
            return reflection.strip()

        if execution_status in {
            "complete",
            "completed",
            "success",
        }:
            return (
                "Falcon completed the requested execution."
            )

        if execution_status == "partial":
            return (
                "Falcon completed part of the requested task, "
                "but the execution was not fully successful."
            )

        return (
            "Falcon could not complete the requested task."
        )

    # ========================================================
    # COMPLETE COGNITION LOOP
    # ========================================================

    def run(
        self,
        goal: str,
        context: dict[str, Any] | None = None,
        username: str = "falcon",
        memories: list | None = None,
        use_web: bool = False,
        use_documents: bool = False,
    ) -> dict[str, Any]:
        """
        Run Falcon's complete cognition pipeline.

        Returns the complete structured task state.
        """

        # ----------------------------------------------------
        # 1. UNDERSTAND
        # ----------------------------------------------------

        state = self.understand(
            goal=goal,
            context=context,
        )

        normalized_goal = state[
            "goal"
        ]

        if not normalized_goal:
            return {
                "task_id": state["task_id"],
                "goal": "",
                "plan": None,
                "execution": {
                    "status": "error",
                    "error": (
                        "Falcon received an empty goal."
                    ),
                },
                "reflection": "",
                "verification": {
                    "verified": False,
                    "reason": (
                        "No goal was provided."
                    ),
                },
                "response": (
                    "Please provide a task for Falcon to complete."
                ),
            }

        # ----------------------------------------------------
        # 2. PLAN
        # ----------------------------------------------------

        try:
            plan = self.plan(
                normalized_goal
            )

        except Exception as exc:
            execution = {
                "status": "error",
                "error": (
                    f"Planning failed: {exc}"
                ),
                "completed_steps": 0,
                "failed_steps": 1,
                "total_steps": 0,
            }

            verification = self.verify(
                question=normalized_goal,
                result=execution,
            )

            response = (
                "Falcon could not create an execution plan: "
                f"{exc}"
            )

            return {
                "task_id": state["task_id"],
                "goal": normalized_goal,
                "context": state["context"],
                "plan": None,
                "execution": execution,
                "reflection": "",
                "verification": verification,
                "response": response,
            }

        # ----------------------------------------------------
        # 3. EXECUTE
        # ----------------------------------------------------

        execution = self.execute(
            plan=plan,
            context=state,
            username=username,
            question=normalized_goal,
            memories=memories,
            use_web=use_web,
            use_documents=use_documents,
        )

        # ----------------------------------------------------
        # 4. CREATE DRAFT
        # ----------------------------------------------------

        draft_answer = self.create_draft(
            goal=normalized_goal,
            execution=execution,
        )

        # ----------------------------------------------------
        # 5. REFLECT
        # ----------------------------------------------------

        reflection = self.reflect(
            question=normalized_goal,
            draft_answer=draft_answer,
        )

        # ----------------------------------------------------
        # 6. VERIFY
        # ----------------------------------------------------

        verification = self.verify(
            question=normalized_goal,
            result=execution,
        )

        # ----------------------------------------------------
        # 7. FINAL SYNTHESIS
        # ----------------------------------------------------

        response = self.synthesize(
            goal=normalized_goal,
            plan=plan,
            execution=execution,
            reflection=reflection,
            verification=verification,
        )

        # ----------------------------------------------------
        # 8. RETURN COMPLETE STATE
        # ----------------------------------------------------

        return {
            "task_id": state["task_id"],
            "goal": normalized_goal,
            "context": state["context"],
            "plan": plan,
            "execution": execution,
            "draft": draft_answer,
            "reflection": reflection,
            "verification": verification,
            "response": response,
        }


# ============================================================
# SHARED INSTANCE
# ============================================================


falcon_intelligence = FalconIntelligence()

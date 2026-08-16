from __future__ import annotations

from typing import Any

from app.agents.business_agent import BUSINESS_PROMPT
from app.agents.coding_agent import CODING_PROMPT
from app.agents.investment_agent import INVESTMENT_PROMPT
from app.agents.research_agent import RESEARCH_PROMPT

from app.agents.planner import create_plan
from app.agents.workflow_engine import execute_workflow
from app.agents.execution_engine import execute_plan
from app.agents.reasoning_engine import reason_about_plan
from app.agents.tool_reasoner import decide_tool_usage

from app.agents.rule_engine import (
    should_use_web,
    should_use_documents,
)

from app.agents.research_engine import (
    build_research_context,
)

from app.agents.collaboration_engine import (
    collaborate,
    synthesize_collaboration,
)

from app.agents.adaptive_execution_engine import (
    execute_adaptively,
)

from app.agents.verification_engine import (
    verify_execution,
)

from app.agents.reflection_engine import (
    reflect,
)

from app.ai_service import ask_ai
from app.core.logger import logger
from app.services.memory_provider import MemoryProvider


# ============================================================
# CONFIGURATION
# ============================================================

memory_provider = MemoryProvider()


AGENT_PROMPTS = {
    "BUSINESS": BUSINESS_PROMPT,
    "CODING": CODING_PROMPT,
    "INVESTMENT": INVESTMENT_PROMPT,
    "RESEARCH": RESEARCH_PROMPT,
}


# ============================================================
# LEGACY SPECIALIST FUNCTIONS
# ============================================================

def run_business_agent(question: str):
    """Run the legacy Business specialist directly."""
    prompt = BUSINESS_PROMPT + "\n\nUser:\n" + str(question or "")
    return ask_ai(prompt)


def run_coding_agent(question: str):
    """Run the legacy Coding specialist directly."""
    prompt = CODING_PROMPT + "\n\nUser:\n" + str(question or "")
    return ask_ai(prompt)


def run_investment_agent(question: str):
    """Run the legacy Investment specialist directly."""
    prompt = INVESTMENT_PROMPT + "\n\nUser:\n" + str(question or "")
    return ask_ai(prompt)


def run_research_agent(question: str):
    """Run the legacy Research specialist directly."""
    prompt = RESEARCH_PROMPT + "\n\nUser:\n" + str(question or "")
    return ask_ai(prompt)


# ============================================================
# SAFE NORMALIZATION HELPERS
# ============================================================

def _safe_dict(value: Any) -> dict[str, Any]:
    """Return a dictionary without raising on unexpected values."""

    if isinstance(value, dict):
        return value

    return {"value": value}


def _safe_list(value: Any) -> list[Any]:
    """Return a list without raising on unexpected values."""

    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def _execution_success(execution: Any) -> bool:
    """
    Determine whether an execution wrapper reports success.

    This intentionally does not treat a merely generated response
    as successful execution.
    """

    if not isinstance(execution, dict):
        return False

    if execution.get("successful") is True:
        return True

    status = str(
        execution.get("status", "")
    ).strip().lower()

    return status in {
        "verified",
        "complete",
        "completed",
        "success",
        "successful",
    }


def _extract_execution_result(
    adaptive_result: Any,
) -> dict[str, Any]:
    """
    Extract the underlying execution result from adaptive execution.

    Adaptive execution normally returns something similar to:

        {
            "status": "...",
            "successful": True,
            "result": {...},
            ...
        }
    """

    if not isinstance(adaptive_result, dict):
        return {
            "status": "failed",
            "successful": False,
            "error": (
                "Adaptive execution returned "
                "an invalid result."
            ),
            "completed_steps": 0,
            "failed_steps": 1,
            "total_steps": 0,
        }

    result = adaptive_result.get("result")

    if isinstance(result, dict):
        return dict(result)

    return {
        "status": str(
            adaptive_result.get(
                "status",
                "failed",
            )
        ),
        "successful": bool(
            adaptive_result.get(
                "successful",
                False,
            )
        ),
        "completed_steps": adaptive_result.get(
            "completed_steps",
            0,
        ),
        "failed_steps": adaptive_result.get(
            "failed_steps",
            0,
        ),
        "total_steps": adaptive_result.get(
            "total_steps",
            0,
        ),
        "error": adaptive_result.get("error"),
    }


# ============================================================
# SYNTHESIS PROMPT
# ============================================================

def _build_synthesis_prompt(
    question: str,
    plan: dict[str, Any],
    workflow: list[Any],
    reasoning: dict[str, Any],
    tool_reasoning: dict[str, Any],
    research_context: Any,
    collaboration_context: dict[str, Any],
    collaboration_synthesis: str,
    shared_context: Any,
    tool_results: dict[str, Any],
    agent_results: dict[str, Any],
    verification: dict[str, Any],
    adaptive_execution: dict[str, Any],
) -> str:
    """
    Build the final grounded synthesis prompt.

    The prompt is returned to chat_service/model_router rather than
    generating a second model response inside this orchestrator.
    """

    return f"""
You are Falcon AI's final answer generation layer.

Your job is to answer the user's actual request using ONLY the
available execution evidence supplied below.

Do not expose Falcon's internal architecture or hidden reasoning.

IMPORTANT GROUNDING RULES:

1. Never invent facts, actions, tool results, citations, files,
   searches, calculations, or completed operations.

2. Never claim that an action happened unless the execution state
   provides evidence that it happened.

3. If an operation failed, say so clearly.

4. If execution was partial, clearly distinguish completed and
   incomplete work.

5. If verification failed, do not present the task as fully verified.

6. Do not treat a plan as proof that an action was executed.

7. Do not treat an intended tool call as a completed tool call.

8. Use research/tool/document results only when they are actually
   present in the supplied execution state.

9. Preserve meaningful uncertainty.

10. Answer the user's request directly.

11. Do not mention internal names such as:
    - orchestrator
    - planner
    - workflow
    - agent
    - reasoning engine
    - adaptive execution
    unless the user explicitly asks about Falcon's architecture.

12. Do not expose hidden chain-of-thought.

13. Be concise when the request is simple and detailed when the
    request requires detail.

14. If there is insufficient evidence to complete the request,
    honestly explain what is missing.

15. Return ONLY the final user-facing answer.

================ USER REQUEST ================

{question}

================ EXECUTION PLAN ================

{plan}

================ WORKFLOW STATE ================

{workflow}

================ PLAN REASONING ================

{reasoning}

================ TOOL DECISION ================

{tool_reasoning}

================ RESEARCH CONTEXT ================

{research_context}

================ TOOL RESULTS ================

{tool_results}

================ SPECIALIST RESULTS ================

{agent_results}

================ COLLABORATION ================

{collaboration_context}

================ COLLABORATIVE SYNTHESIS ================

{collaboration_synthesis}

================ SHARED CONTEXT ================

{shared_context}

================ VERIFICATION ================

{verification}

================ ADAPTIVE EXECUTION ================

{adaptive_execution}

================ FINAL INSTRUCTION ================

Produce the best accurate answer to the user's request.
"""


# ============================================================
# MAIN ORCHESTRATION
# ============================================================

def orchestrate(
    db,
    username: str,
    question: str,
) -> dict[str, Any]:
    """
    Canonical Falcon cognitive orchestration pipeline.

    Pipeline:

        User request
            ↓
        Planner
            ↓
        Workflow preparation
            ↓
        Plan reasoning
            ↓
        Tool decision
            ↓
        Capability checks
            ↓
        Memory retrieval
            ↓
        Adaptive execution
            ↓
        Verification
            ↓
        Research context
            ↓
        Multi-agent collaboration
            ↓
        Collaboration synthesis
            ↓
        Grounded synthesis prompt
            ↓
        Model router / chat service

    IMPORTANT:

    This function prepares the grounded synthesis prompt.

    The actual final model response is generated by the caller
    (currently chat_service) through the central model router.

    This prevents Falcon from unnecessarily generating two final
    model responses for one chat request.
    """

    question = str(
        question or ""
    ).strip()

    if not question:
        return {
            "error": True,
            "message": (
                "Please provide a question or task."
            ),
        }

    logger.info(
        "Falcon orchestration started for user '%s'.",
        username,
    )

    try:
        # ========================================================
        # 1. CREATE PLAN
        # ========================================================

        plan = _safe_dict(
            create_plan(question)
        )

        logger.info(
            "Falcon execution plan created."
        )

        # ========================================================
        # 2. PREPARE WORKFLOW
        # ========================================================

        try:
            workflow = _safe_list(
                execute_workflow(plan)
            )
        except Exception:
            logger.exception(
                "Workflow preparation failed."
            )
            workflow = []

        logger.info(
            "Falcon workflow prepared with %s steps.",
            len(workflow),
        )

        # ========================================================
        # 3. PLAN REASONING
        # ========================================================

        try:
            reasoning = _safe_dict(
                reason_about_plan(
                    question=question,
                    plan=plan,
                )
            )
        except Exception:
            logger.exception(
                "Plan reasoning failed."
            )
            reasoning = {
                "status": "unavailable",
                "error": "Plan reasoning unavailable.",
            }

        # ========================================================
        # 4. TOOL DECISION
        # ========================================================

        try:
            tool_reasoning = _safe_dict(
                decide_tool_usage(
                    question=question,
                    plan=plan,
                )
            )
        except Exception:
            logger.exception(
                "Tool decision failed."
            )
            tool_reasoning = {
                "status": "unavailable",
                "error": "Tool decision unavailable.",
            }

        # ========================================================
        # 5. CAPABILITY CHECKS
        # ========================================================

        try:
            use_web = bool(
                should_use_web(question)
            )
        except Exception:
            logger.exception(
                "Web capability check failed."
            )
            use_web = False

        try:
            use_documents = bool(
                should_use_documents(question)
            )
        except Exception:
            logger.exception(
                "Document capability check failed."
            )
            use_documents = False

        logger.info(
            "Falcon capability checks: web=%s documents=%s",
            use_web,
            use_documents,
        )

        # ========================================================
        # 6. MEMORY RETRIEVAL
        # ========================================================

        memories: list[Any] = []

        try:
            memories = _safe_list(
                memory_provider.search(
                    db,
                    username,
                    question,
                )
            )

            logger.info(
                "Falcon retrieved %s memory entries.",
                len(memories),
            )

        except Exception:
            logger.exception(
                "Memory retrieval failed."
            )
            memories = []

        # ========================================================
        # 7. ADAPTIVE EXECUTION
        # ========================================================

        try:
            adaptive_result = execute_adaptively(
                username=username,
                question=question,
                plan=plan,
                execute_fn=execute_plan,
                verify_fn=verify_execution,
                memories=memories,
                use_web=use_web,
                use_documents=use_documents,
            )

            adaptive_result = _safe_dict(
                adaptive_result
            )

        except Exception as exc:
            logger.exception(
                "Adaptive execution failed."
            )

            adaptive_result = {
                "status": "failed",
                "successful": False,
                "error": str(exc),
                "rounds": 0,
                "history": [],
                "recovery": {},
                "verification": {
                    "verified": False,
                    "reason": (
                        "Adaptive execution failed."
                    ),
                },
                "final_plan": plan,
            }

        logger.info(
            "Falcon adaptive execution finished: "
            "status=%s successful=%s rounds=%s",
            adaptive_result.get(
                "status",
                "unknown",
            ),
            adaptive_result.get(
                "successful",
                False,
            ),
            adaptive_result.get(
                "rounds",
                0,
            ),
        )

        # ========================================================
        # 8. EXTRACT EXECUTION RESULT
        # ========================================================

        execution_results = _extract_execution_result(
            adaptive_result
        )

        # ========================================================
        # 9. VERIFICATION
        # ========================================================

        verification = adaptive_result.get(
            "verification",
            {},
        )

        if not isinstance(
            verification,
            dict,
        ):
            verification = {
                "verified": False,
                "reason": (
                    "No valid verification result was returned."
                ),
            }

        # If adaptive execution did not provide verification,
        # perform one final deterministic verification pass.
        if "verified" not in verification:
            try:
                verification = _safe_dict(
                    verify_execution(
                        question=question,
                        result=execution_results,
                    )
                )
            except Exception:
                logger.exception(
                    "Final verification failed."
                )
                verification = {
                    "verified": False,
                    "reason": (
                        "Final verification could not be completed."
                    ),
                }

        # ========================================================
        # 10. ADAPTIVE EXECUTION METADATA
        # ========================================================

        execution_results[
            "adaptive_execution"
        ] = {
            "status": adaptive_result.get(
                "status",
                "unknown",
            ),
            "successful": adaptive_result.get(
                "successful",
                False,
            ),
            "rounds": adaptive_result.get(
                "rounds",
                0,
            ),
            "history": adaptive_result.get(
                "history",
                [],
            ),
            "recovery": adaptive_result.get(
                "recovery",
                {},
            ),
            "verification": verification,
            "final_plan": adaptive_result.get(
                "final_plan",
                plan,
            ),
        }

        # ========================================================
        # 11. EXTRACT TOOL / AGENT / SHARED RESULTS
        # ========================================================

        tool_results = _safe_dict(
            execution_results.get(
                "tools",
                {},
            )
        )

        agent_results = _safe_dict(
            execution_results.get(
                "agents",
                {},
            )
        )

        shared_context = execution_results.get(
            "context_snapshot",
            execution_results.get(
                "context",
                {},
            ),
        )

        # ========================================================
        # 12. RESEARCH CONTEXT
        # ========================================================

        web_results = tool_results.get(
            "web",
            tool_results.get(
                "web_search",
                [],
            ),
        )

        try:
            research_context = build_research_context(
                web_results
            )
        except Exception:
            logger.exception(
                "Research context construction failed."
            )
            research_context = ""

        # ========================================================
        # 13. MULTI-AGENT COLLABORATION
        # ========================================================

        try:
            collaboration_context = _safe_dict(
                collaborate(agent_results)
            )
        except Exception:
            logger.exception(
                "Multi-agent collaboration failed."
            )

            collaboration_context = {
                "agents": [],
                "conflicts": [],
                "assessment": "",
                "confidence": 0.0,
            }

        # ========================================================
        # 14. COLLABORATIVE SYNTHESIS
        # ========================================================

        try:
            collaboration_synthesis = str(
                synthesize_collaboration(
                    question=question,
                    collaboration=collaboration_context,
                )
                or ""
            ).strip()

        except Exception:
            logger.exception(
                "Collaboration synthesis failed."
            )
            collaboration_synthesis = ""

        # ========================================================
        # 15. BUILD GROUNDED SYNTHESIS PROMPT
        # ========================================================

        synthesis_prompt = _build_synthesis_prompt(
            question=question,
            plan=plan,
            workflow=workflow,
            reasoning=reasoning,
            tool_reasoning=tool_reasoning,
            research_context=research_context,
            collaboration_context=collaboration_context,
            collaboration_synthesis=collaboration_synthesis,
            shared_context=shared_context,
            tool_results=tool_results,
            agent_results=agent_results,
            verification=verification,
            adaptive_execution=adaptive_result,
        )

        # ========================================================
        # 16. EXECUTION SUMMARY
        # ========================================================

        execution_status = str(
            execution_results.get(
                "status",
                adaptive_result.get(
                    "status",
                    "unknown",
                ),
            )
        )

        completed_steps = execution_results.get(
            "completed_steps",
            0,
        )

        failed_steps = execution_results.get(
            "failed_steps",
            0,
        )

        total_steps = execution_results.get(
            "total_steps",
            len(
                plan.get(
                    "steps",
                    [],
                )
            ),
        )

        adaptive_successful = _execution_success(
            adaptive_result
        )

        verified = bool(
            verification.get(
                "verified",
                False,
            )
        )

        successful_execution = (
            adaptive_successful
            and verified
        )

        # ========================================================
        # 17. OPTIONAL INTERNAL REFLECTION
        # ========================================================

        reflection = ""

        try:
            reflection_input = {
                "status": execution_status,
                "successful": successful_execution,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "total_steps": total_steps,
                "verification": verification,
                "tools": tool_results,
                "agents": agent_results,
            }

            reflection_result = reflect(
                question=question,
                draft_answer=str(
                    reflection_input
                ),
            )

            reflection = str(
                reflection_result or ""
            ).strip()

        except Exception:
            logger.exception(
                "Execution reflection failed."
            )

        # ========================================================
        # 18. RETURN COMPLETE ORCHESTRATION STATE
        # ========================================================

        result = {
            # Compatibility / user-facing field.
            #
            # chat_service normally generates the actual answer
            # through model_router using synthesis_prompt.
            "answer": "",

            # IMPORTANT:
            # chat_service.py expects this field.
            "synthesis_prompt": synthesis_prompt,

            # Structured execution state.
            "execution": {
                "status": execution_status,
                "successful": successful_execution,
                "adaptive_status": adaptive_result.get(
                    "status",
                    "unknown",
                ),
                "adaptive_successful": adaptive_result.get(
                    "successful",
                    False,
                ),
                "adaptive_rounds": adaptive_result.get(
                    "rounds",
                    0,
                ),
                "verification": verification,
                "plan": plan,
                "workflow": workflow,
                "reasoning": reasoning,
                "tool_reasoning": tool_reasoning,
                "use_web": use_web,
                "use_documents": use_documents,
                "memory_count": len(memories),
                "results": agent_results,
                "tool_results": tool_results,
                "collaboration": collaboration_context,
                "collaboration_synthesis": (
                    collaboration_synthesis
                ),
                "shared_context": shared_context,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "total_steps": total_steps,
                "adaptive_history": adaptive_result.get(
                    "history",
                    [],
                ),
                "reflection": reflection,
            },

            # Useful top-level metadata for API consumers.
            "verification": verification,
            "plan": plan,
            "workflow": workflow,
            "reasoning": reasoning,
            "tool_reasoning": tool_reasoning,
            "use_web": use_web,
            "use_documents": use_documents,
            "memory_count": len(memories),
            "collaboration": collaboration_context,
            "collaboration_synthesis": (
                collaboration_synthesis
            ),
        }

        logger.info(
            "Falcon orchestration finished: "
            "status=%s successful=%s completed=%s failed=%s total=%s",
            execution_status,
            successful_execution,
            completed_steps,
            failed_steps,
            total_steps,
        )

        return result

    except Exception as exc:
        logger.exception(
            "Falcon orchestrator failed."
        )

        return {
            "error": True,
            "message": (
                "Falcon encountered an internal processing "
                "error while completing the request."
            ),
            "details": str(exc),
            "synthesis_prompt": "",
        }

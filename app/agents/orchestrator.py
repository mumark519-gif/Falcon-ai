from __future__ import annotations

from typing import Any

from app.agents.business_agent import BUSINESS_PROMPT
from app.agents.coding_agent import CODING_PROMPT
from app.agents.investment_agent import INVESTMENT_PROMPT
from app.agents.research_agent import RESEARCH_PROMPT

from app.agents.planner import create_plan
from app.agents.workflow_engine import execute_workflow
from app.agents.execution_engine import execute_plan

from app.agents.reasoning_engine import (
    reason_about_plan,
)

from app.agents.tool_reasoner import (
    decide_tool_usage,
)

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

from app.agents.reflection_engine import (
    reflect,
)

from app.agents.adaptive_execution_engine import (
    execute_adaptively,
)

from app.agents.verification_engine import (
    verify_execution,
)

from app.ai_service import ask_ai
from app.core.logger import logger

from app.services.memory_provider import (
    MemoryProvider,
)


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

def run_business_agent(
    question: str,
):
    """
    Legacy-compatible direct Business agent.
    """

    prompt = (
        BUSINESS_PROMPT
        + "\n\nUser:\n"
        + question
    )

    return ask_ai(prompt)


def run_coding_agent(
    question: str,
):
    """
    Legacy-compatible direct Coding agent.
    """

    prompt = (
        CODING_PROMPT
        + "\n\nUser:\n"
        + question
    )

    return ask_ai(prompt)


def run_investment_agent(
    question: str,
):
    """
    Legacy-compatible direct Investment agent.
    """

    prompt = (
        INVESTMENT_PROMPT
        + "\n\nUser:\n"
        + question
    )

    return ask_ai(prompt)


def run_research_agent(
    question: str,
):
    """
    Legacy-compatible direct Research agent.
    """

    prompt = (
        RESEARCH_PROMPT
        + "\n\nUser:\n"
        + question
    )

    return ask_ai(prompt)


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _safe_dict(
    value: Any,
) -> dict:
    """
    Convert arbitrary values into a dictionary when possible.
    """

    if isinstance(value, dict):
        return value

    return {
        "value": value,
    }


def _safe_list(
    value: Any,
) -> list:
    """
    Convert arbitrary values into a list.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def _execution_success(
    execution: dict,
) -> bool:
    """
    Determine whether adaptive execution produced
    a successful final result.
    """

    if not isinstance(
        execution,
        dict,
    ):
        return False

    if execution.get(
        "successful",
        False,
    ):
        return True

    status = str(
        execution.get(
            "status",
            "",
        )
    ).strip().lower()

    return status in {
        "verified",
        "complete",
        "completed",
        "success",
    }


def _extract_execution_result(
    adaptive_result: Any,
) -> dict:
    """
    Extract the actual execution-engine result from the
    adaptive execution wrapper.

    Adaptive execution returns:

        {
            "status": ...,
            "successful": ...,
            "result": {...},
            ...
        }

    This helper safely extracts the nested result.
    """

    if not isinstance(
        adaptive_result,
        dict,
    ):
        return {
            "status": "failed",
            "error": (
                "Adaptive execution returned "
                "an invalid result."
            ),
            "completed_steps": 0,
            "failed_steps": 1,
            "total_steps": 0,
        }

    result = adaptive_result.get(
        "result"
    )

    if isinstance(
        result,
        dict,
    ):
        return result

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
        "error": adaptive_result.get(
            "error"
        ),
    }


def _build_synthesis_prompt(
    question: str,
    plan: dict,
    workflow: list,
    reasoning: dict,
    tool_reasoning: dict,
    research_context: Any,
    collaboration_context: dict,
    collaboration_synthesis: str,
    shared_context: Any,
    tool_results: dict,
    agent_results: dict,
    verification: dict,
    adaptive_execution: dict,
) -> str:
    """
    Build Falcon's final synthesis prompt.
    """

    prompt = """
You are Falcon AI's Final Synthesis Engine.

Your responsibility is to produce the final answer to the
user using the execution results supplied below.

The system may have used:

- specialist agents
- web search
- document search
- Python
- browser
- persistent memory
- multi-agent collaboration
- reasoning
- adaptive execution
- verification
- reflection

Rules:

1. Answer the user's actual question directly.

2. Use the strongest available evidence.

3. Do not invent facts.

4. Do not claim that a tool was used unless the execution
   results demonstrate that it actually ran.

5. Distinguish facts from assumptions.

6. Resolve contradictions when reliable evidence allows it.

7. Preserve meaningful uncertainty.

8. Do not expose internal Falcon architecture unless it is
   relevant to the user.

9. Do not mention "agents", "planner", "workflow", or
   "orchestrator" merely because they were used internally.

10. If the user asked for a concrete task, prioritize
    completing the task rather than describing how Falcon
    thinks.

11. If execution results are incomplete, acknowledge what
    could not be verified.

12. Be clear, useful, accurate, and non-repetitive.

13. If only one specialist produced useful information,
    improve and present that information naturally.

14. If multiple specialists produced useful information,
    merge them into one coherent answer.

15. Do not blindly trust a low-confidence result.

16. Verification information is evidence about whether the
    execution completed correctly. Do not treat verification
    as user-facing content unless relevant.

17. Return ONLY the final answer.

"""

    prompt += (
        "\n\n================ USER QUESTION ================\n"
        + question
    )

    prompt += (
        "\n\n================ EXECUTION PLAN ================\n"
        + str(plan)
    )

    prompt += (
        "\n\n================ WORKFLOW STATE ================\n"
        + str(workflow)
    )

    prompt += (
        "\n\n================ PLAN REASONING ================\n"
        + str(reasoning)
    )

    prompt += (
        "\n\n================ TOOL REASONING ================\n"
        + str(tool_reasoning)
    )

    prompt += (
        "\n\n================ RESEARCH CONTEXT ================\n"
        + str(research_context)
    )

    prompt += (
        "\n\n================ TOOL RESULTS ================\n"
        + str(tool_results)
    )

    prompt += (
        "\n\n================ AGENT RESULTS ================\n"
        + str(agent_results)
    )

    prompt += (
        "\n\n================ COLLABORATION ================\n"
        + str(collaboration_context)
    )

    prompt += (
        "\n\n================ COLLABORATION SYNTHESIS ================\n"
        + str(collaboration_synthesis)
    )

    prompt += (
        "\n\n================ SHARED CONTEXT ================\n"
        + str(shared_context)
    )

    prompt += (
        "\n\n================ VERIFICATION ================\n"
        + str(verification)
    )

    prompt += (
        "\n\n================ ADAPTIVE EXECUTION ================\n"
        + str(adaptive_execution)
    )

    return prompt


# ============================================================
# MAIN ORCHESTRATION
# ============================================================

def orchestrate(
    db,
    username: str,
    question: str,
):
    """
    Falcon's central cognitive orchestration pipeline.

    Pipeline:

        User
          ↓
        Planner
          ↓
        Workflow preparation
          ↓
        Plan reasoning
          ↓
        Tool reasoning
          ↓
        Rule checks
          ↓
        Memory retrieval
          ↓
        Adaptive execution
          ↓
        Verification
          ↓
        Shared context
          ↓
        Multi-agent collaboration
          ↓
        Collaboration synthesis
          ↓
        Final synthesis
          ↓
        Reflection
          ↓
        Final answer

    The orchestrator coordinates the system but does not itself
    execute individual tools or specialist agents.
    """

    question = (
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

        # ====================================================
        # 1. CREATE PLAN
        # ====================================================

        plan = create_plan(
            question
        )

        plan = _safe_dict(
            plan
        )

        logger.info(
            "Falcon execution plan created: %s",
            plan,
        )

        # ====================================================
        # 2. PREPARE WORKFLOW
        # ====================================================

        workflow = execute_workflow(
            plan
        )

        workflow = _safe_list(
            workflow
        )

        logger.info(
            "Falcon workflow prepared with %s steps.",
            len(workflow),
        )

        # ====================================================
        # 3. REASON ABOUT PLAN
        # ====================================================

        reasoning = reason_about_plan(
            question=question,
            plan=plan,
        )

        reasoning = _safe_dict(
            reasoning
        )

        # ====================================================
        # 4. DETERMINE TOOL REQUIREMENTS
        # ====================================================

        tool_reasoning = decide_tool_usage(
            question=question,
            plan=plan,
        )

        tool_reasoning = _safe_dict(
            tool_reasoning
        )

        # ====================================================
        # 5. RULE-BASED CAPABILITY CHECKS
        # ====================================================

        use_web = bool(
            should_use_web(
                question
            )
        )

        use_documents = bool(
            should_use_documents(
                question
            )
        )

        logger.info(
            "Falcon capability checks: web=%s documents=%s",
            use_web,
            use_documents,
        )

        # ====================================================
        # 6. RETRIEVE MEMORY
        # ====================================================

        memories = []

        try:

            memories = memory_provider.search(
                db,
                username,
                question,
            )

            memories = _safe_list(
                memories
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

        # ====================================================
        # 7. ADAPTIVE EXECUTION
        # ====================================================

        adaptive_result = execute_adaptively(
            username=username,
            question=question,
            plan=plan,

            # THIS IS THE IMPORTANT FIX.
            #
            # adaptive_execution_engine.py requires
            # an execute_fn.
            #
            # Falcon's existing execution_engine.py provides
            # execute_plan.
            execute_fn=execute_plan,

            # Verification is performed inside the adaptive
            # execution cycle after each successful round.
            verify_fn=verify_execution,

            memories=memories,
            use_web=use_web,
            use_documents=use_documents,
        )

        adaptive_result = _safe_dict(
            adaptive_result
        )

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

        # ====================================================
        # 8. EXTRACT ACTUAL EXECUTION RESULT
        # ====================================================

        execution_results = (
            _extract_execution_result(
                adaptive_result
            )
        )

        execution_results = _safe_dict(
            execution_results
        )

        # ====================================================
        # 9. GET VERIFICATION RESULT
        # ====================================================

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
                    "No valid verification result."
                ),
            }

        # ====================================================
        # 10. STORE ADAPTIVE EXECUTION METADATA
        # ====================================================

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

        logger.info(
            "Falcon execution result status=%s.",
            execution_results.get(
                "status",
                "unknown",
            ),
        )

        # ====================================================
        # 11. EXTRACT RESULTS
        # ====================================================

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

        # ====================================================
        # 12. BUILD RESEARCH CONTEXT
        # ====================================================

        web_results = tool_results.get(
            "web",
            tool_results.get(
                "web_search",
                [],
            ),
        )

        try:

            research_context = (
                build_research_context(
                    web_results
                )
            )

        except Exception:

            logger.exception(
                "Research context construction failed."
            )

            research_context = ""

        # ====================================================
        # 13. MULTI-AGENT COLLABORATION
        # ====================================================

        try:

            collaboration_context = collaborate(
                agent_results
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

        collaboration_context = _safe_dict(
            collaboration_context
        )

        # ====================================================
        # 14. COLLABORATIVE SYNTHESIS
        # ====================================================

        try:

            collaboration_synthesis = (
                synthesize_collaboration(
                    question=question,
                    collaboration=collaboration_context,
                )
            )

        except Exception:

            logger.exception(
                "Collaboration synthesis failed."
            )

            collaboration_synthesis = ""

        collaboration_synthesis = str(
            collaboration_synthesis or ""
        ).strip()

        # ====================================================
        # 15. FINAL SYNTHESIS
        # ====================================================

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

        draft_answer = ask_ai(
            synthesis_prompt
        )

        draft_answer = str(
            draft_answer or ""
        ).strip()

        if not draft_answer:

            draft_answer = (
                "Falcon completed the requested processing "
                "but did not receive a usable synthesis."
            )

        # ====================================================
        # 16. REFLECTION / QUALITY CONTROL
        # ====================================================

        try:

            final_answer = reflect(
                question=question,
                draft_answer=draft_answer,
            )

            final_answer = str(
                final_answer or ""
            ).strip()

        except Exception:

            logger.exception(
                "Reflection engine failed."
            )

            final_answer = draft_answer

        if not final_answer:

            final_answer = draft_answer

        # ====================================================
        # 17. FINAL EXECUTION SUMMARY
        # ====================================================

        execution_status = execution_results.get(
            "status",
            "unknown",
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

        successful_execution = (
            _execution_success(
                adaptive_result
            )
            and bool(
                verification.get(
                    "verified",
                    False,
                )
            )
        )

        # ====================================================
        # 18. RETURN COMPLETE RESULT
        # ====================================================

        result = {
            "answer": final_answer,

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

                "memory_count": len(
                    memories
                ),

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
            },
        }

        logger.info(
            "Falcon orchestration finished: "
            "status=%s completed=%s failed=%s total=%s",
            execution_status,
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
        }
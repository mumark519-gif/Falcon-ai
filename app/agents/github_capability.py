from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re

from app.core.logger import logger


# ============================================================
# GITHUB OPERATIONS
# ============================================================

GITHUB_OPERATIONS = {
    "inspect_pull_request_reviews": {
        "description": "Inspect pull request reviews and reviewer feedback.",
        "priority": 90,
        "write": False,
        "approval": False,
    },
    "compare_commits": {
        "description": "Compare commits or revisions.",
        "priority": 80,
        "write": False,
        "approval": False,
    },
    "create_commit": {
        "description": "Create a Git commit.",
        "priority": 80,
        "write": True,
        "approval": True,
    },
    "resolve_review_thread": {
        "description": "Resolve a pull request review thread.",
        "priority": 90,
        "write": True,
        "approval": True,
    },
    "rerun_failed_job": {
        "description": "Rerun a failed GitHub Actions job.",
        "priority": 90,
        "write": True,
        "approval": True,
    },
    "inspect_review_threads": {
        "description": "Inspect unresolved or existing pull request review threads.",
        "priority": 95,
        "write": False,
        "approval": False,
    },
    "update_file": {
        "description": "Update an existing repository file.",
        "priority": 80,
        "write": True,
        "approval": True,
    },
    "delete_file": {
        "description": "Delete a repository file.",
        "priority": 75,
        "write": True,
        "approval": True,
    },
    "read_pull_request": {
        "description": "Read pull request information.",
        "priority": 85,
        "write": False,
        "approval": False,
    },
    "inspect_branch": {
        "description": "Inspect a repository branch.",
        "priority": 70,
        "write": False,
        "approval": False,
    },
    "create_file": {
        "description": "Create a new repository file.",
        "priority": 80,
        "write": True,
        "approval": True,
    },
    "read_file": {
        "description": "Read a repository file.",
        "priority": 85,
        "write": False,
        "approval": False,
    },
    "read_issue": {
        "description": "Read a GitHub issue.",
        "priority": 75,
        "write": False,
        "approval": False,
    },
    "inspect_workflow": {
        "description": "Inspect a GitHub Actions workflow.",
        "priority": 80,
        "write": False,
        "approval": False,
    },
    "create_pull_request": {
        "description": "Create or open a pull request.",
        "priority": 100,
        "write": True,
        "approval": True,
    },
    "list_issues": {
        "description": "List repository issues.",
        "priority": 70,
        "write": False,
        "approval": False,
    },
    "search_code": {
        "description": "Search repository code.",
        "priority": 75,
        "write": False,
        "approval": False,
    },
    "list_pull_requests": {
        "description": "List pull requests.",
        "priority": 80,
        "write": False,
        "approval": False,
    },
    "list_branches": {
        "description": "List repository branches.",
        "priority": 65,
        "write": False,
        "approval": False,
    },
    "inspect_logs": {
        "description": "Inspect GitHub Actions or repository logs.",
        "priority": 75,
        "write": False,
        "approval": False,
    },
    "update_issue": {
        "description": "Update an existing GitHub issue.",
        "priority": 75,
        "write": True,
        "approval": True,
    },
    "create_issue": {
        "description": "Create a GitHub issue.",
        "priority": 75,
        "write": True,
        "approval": True,
    },
    "create_branch": {
        "description": "Create a repository branch.",
        "priority": 75,
        "write": True,
        "approval": True,
    },
    "inspect_job": {
        "description": "Inspect a GitHub Actions job.",
        "priority": 80,
        "write": False,
        "approval": False,
    },
    "inspect_commit": {
        "description": "Inspect a specific commit.",
        "priority": 75,
        "write": False,
        "approval": False,
    },
    "inspect_pull_request_files": {
        "description": "Inspect files changed by a pull request.",
        "priority": 90,
        "write": False,
        "approval": False,
    },
    "inspect_actions": {
        "description": "Inspect GitHub Actions workflows, runs and jobs.",
        "priority": 85,
        "write": False,
        "approval": False,
    },
    "inspect_pull_request_diff": {
        "description": "Inspect the diff of a pull request.",
        "priority": 90,
        "write": False,
        "approval": False,
    },
    "inspect_repository": {
        "description": "Inspect repository information.",
        "priority": 50,
        "write": False,
        "approval": False,
    },
}


# ============================================================
# SIGNAL DEFINITIONS
# ============================================================

GITHUB_SIGNALS = {
    "inspect_pull_request_reviews": [
        "pull request review",
        "pull request reviews",
        "pr review",
        "pr reviews",
        "review on my pr",
        "reviews on my pr",
        "review feedback on my pr",
        "review feedback",
    ],

    "compare_commits": [
        "compare commits",
        "compare commit",
        "compare these commits",
        "compare two commits",
        "diff between commits",
    ],

    "create_commit": [
        "create a commit",
        "create commit",
        "make a commit",
        "commit these changes",
        "commit changes",
    ],

    "resolve_review_thread": [
        "resolve review thread",
        "resolve the review thread",
        "resolve review threads",
        "resolve this review thread",
        "mark review thread resolved",
        "mark this review thread resolved",
    ],

    "rerun_failed_job": [
        "rerun failed job",
        "rerun the failed job",
        "rerun failed github actions job",
        "rerun the failed github actions job",
        "rerun github actions job",
        "rerun actions job",
        "retry failed github actions",
        "retry the failed github actions",
        "run the failed job again",
        "run failed job again",
    ],

    "inspect_review_threads": [
        "inspect review threads",
        "inspect review thread",
        "show review threads",
        "show unresolved review threads",
        "list review threads",
        "unresolved review comments",
        "unresolved review threads",
        "review threads on my pr",
        "review comments on my pr",
        "review comments on this pr",
    ],

    "update_file": [
        "update file",
        "update the file",
        "edit file",
        "edit the file",
        "modify file",
        "modify the file",
        "change the file",
    ],

    "delete_file": [
        "delete file",
        "delete the file",
        "remove file",
        "remove the file",
    ],

    "read_pull_request": [
        "inspect my github pull request",
        "inspect this github pull request",
        "inspect the github pull request",
        "inspect my pull request",
        "inspect this pull request",
        "inspect the pull request",
        "read my github pull request",
        "read this github pull request",
        "read my pull request",
        "read this pull request",
        "read the pull request",
        "show me the pull request",
        "show this pull request",
        "show the pull request",
        "what is in this pull request",
        "tell me about this pull request",
        "pull request details",
        "pull request information",
        "read pull request",
        "show pull request",
        "inspect pull request",
        "pull request details",
        "pr details",
        "inspect pr",
        "show pr",
        "read pr",
    ],

    "inspect_branch": [
        "inspect branch",
        "inspect the branch",
        "show branch",
        "branch details",
        "branch information",
    ],

    "create_file": [
        "create file",
        "create the file",
        "add file",
        "add a file",
        "create a new file",
        "create new file",
    ],

    "read_file": [
        "read file",
        "read the file",
        "show file",
        "show the file",
        "open file",
        "open the file",
        "contents of the file",
        "file contents",
        "read readme",
        "read the readme",
        "show readme",
        "show the readme",
        "open readme",
        "open the readme",
        "read readme file",
        "read the readme file",
        "show readme file",
        "show the readme file",
    ],

    "read_issue": [
        "read issue",
        "read the issue",
        "show issue",
        "show the issue",
        "inspect issue",
        "issue details",
    ],

    "inspect_workflow": [
        "inspect workflow",
        "inspect the workflow",
        "show workflow",
        "workflow details",
        "workflow configuration",
        "github actions workflow",
    ],

    "create_pull_request": [
        "create pull request",
        "create a pull request",
        "create the pull request",
        "open pull request",
        "open a pull request",
        "open the pull request",
        "make a pull request",
        "make pull request",
        "create pr",
        "create a pr",
        "open pr",
        "open a pr",
        "make a pr",
        "submit pull request",
        "submit a pull request",
    ],

    "list_issues": [
        "list issues",
        "list the issues",
        "show issues",
        "show all issues",
        "list github issues",
        "list repository issues",
    ],

    "search_code": [
        "search code",
        "search the code",
        "search repository code",
        "find code",
        "find this code",
        "search github code",
    ],

    "list_pull_requests": [
        "list pull requests",
        "list pull request",
        "show pull requests",
        "show all pull requests",
        "list prs",
        "list pr",
        "show prs",
        "show pr list",
    ],

    "list_branches": [
        "list branches",
        "list branch",
        "show branches",
        "show all branches",
        "repository branches",
    ],

    "inspect_logs": [
        "inspect logs",
        "inspect the logs",
        "show logs",
        "github actions logs",
        "actions logs",
        "workflow logs",
        "job logs",
        "failed job logs",
    ],

    "update_issue": [
        "update issue",
        "update the issue",
        "edit issue",
        "edit the issue",
        "modify issue",
    ],

    "create_issue": [
        "create issue",
        "create an issue",
        "create a github issue",
        "open issue",
        "open an issue",
    ],

    "create_branch": [
        "create branch",
        "create a branch",
        "make branch",
        "make a branch",
        "new branch",
    ],

    "inspect_job": [
        "inspect job",
        "inspect the job",
        "show job",
        "job details",
        "github actions job",
        "actions job",
        "failed actions job",
    ],

    "inspect_commit": [
        "inspect commit",
        "inspect the commit",
        "show commit",
        "commit details",
        "commit information",
    ],

    "inspect_pull_request_files": [
        "files changed in pr",
        "files changed in pull request",
        "files changed by pr",
        "files changed by pull request",
        "changed files in pr",
        "changed files in pull request",
        "show changed files",
        "show me the files changed",
        "show files changed",
        "list changed files",
        "what files changed in pr",
        "what files changed in the pr",
        "which files changed in pr",
        "which files changed in the pr",
        "pr changed files",
        "pull request changed files",
    ],

    "inspect_actions": [
        "github actions",
        "github action",
        "actions run",
        "actions runs",
        "actions status",
        "workflow run",
        "workflow runs",
        "github actions run",
        "github actions job",
    ],

    "inspect_pull_request_diff": [
        "pull request diff",
        "pull request changes",
        "pr diff",
        "pr changes",
        "show pr diff",
        "show pull request diff",
        "inspect pr diff",
        "inspect pull request diff",
        "what changed in this pr",
        "what changed in the pr",
        "show changes in pr",
        "show changes in the pull request",
    ],

    "inspect_repository": [
        "inspect repository",
        "inspect repo",
        "repository information",
        "repository details",
        "repo information",
        "repo details",
        "show repository",
    ],
}


# ============================================================
# ROUTE OBJECT
# ============================================================

@dataclass
class GitHubRoute:
    operation: str = "inspect_repository"

    confidence: float = 0.25

    requires_write_permission: bool = False

    requires_approval: bool = False

    matched_signals: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "confidence": self.confidence,
            "requires_write_permission": (
                self.requires_write_permission
            ),
            "requires_approval": (
                self.requires_approval
            ),
            "matched_signals": self.matched_signals,
            "metadata": self.metadata,
        }


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize_question(
    question: str,
) -> str:
    return " ".join(
        str(question or "")
        .lower()
        .strip()
        .split()
    )


# ============================================================
# SIGNAL MATCHING
# ============================================================

def _signal_matches(
    question: str,
    signal: str,
) -> bool:
    """
    Match a natural-language GitHub signal.

    Short/simple phrases use word-boundary matching so that
    words such as:

        resolve

    do NOT accidentally match:

        unresolved

    Longer phrases use substring matching because GitHub
    requests naturally contain those phrases.
    """

    signal = signal.strip().lower()

    if not signal:
        return False

    if len(signal.split()) <= 2:
        pattern = rf"\b{re.escape(signal)}\b"
        return re.search(
            pattern,
            question,
        ) is not None

    return signal in question


def _score_operation(
    question: str,
    operation: str,
) -> tuple[int, list[str]]:
    """
    Calculate deterministic operation score.
    """

    signals = GITHUB_SIGNALS.get(
        operation,
        [],
    )

    score = 0
    matched = []

    for signal in signals:

        if not _signal_matches(
            question,
            signal,
        ):
            continue

        words = len(
            signal.split()
        )

        if words >= 5:
            weight = 4
        elif words >= 3:
            weight = 3
        elif words == 2:
            weight = 2
        else:
            weight = 1

        score += weight
        matched.append(signal)

    return score, matched


# ============================================================
# SPECIALIZED DISAMBIGUATION
# ============================================================

def _apply_special_cases(
    question: str,
    scores: dict[str, int],
    matched: dict[str, list[str]],
) -> None:
    """
    Resolve common GitHub language where several operations
    can receive overlapping signals.
    """

    # --------------------------------------------------------
    # PR creation must win over generic PR inspection.
    # --------------------------------------------------------

    creation_phrases = (
        "create pull request",
        "create a pull request",
        "create the pull request",
        "create pr",
        "create a pr",
        "open pull request",
        "open a pull request",
        "open pr",
        "open a pr",
        "make a pull request",
        "make pull request",
        "make a pr",
        "submit pull request",
        "submit a pull request",
    )

    creation_matches = [
        phrase
        for phrase in creation_phrases
        if phrase in question
    ]

    if creation_matches:
        scores[
            "create_pull_request"
        ] = max(
            scores.get(
                "create_pull_request",
                0,
            ),
            8,
        )

        matched[
            "create_pull_request"
        ] = list(
            dict.fromkeys(
                matched.get(
                    "create_pull_request",
                    [],
                )
                + creation_matches
            )
        )

    # --------------------------------------------------------
    # Changed files in a PR.
    # --------------------------------------------------------

    changed_file_phrases = (
        "files changed",
        "changed files",
        "files changed in",
        "files changed by",
        "which files changed",
        "what files changed",
    )

    if (
        (
            "pr" in question
            or "pull request" in question
        )
        and any(
            phrase in question
            for phrase in changed_file_phrases
        )
    ):
        scores[
            "inspect_pull_request_files"
        ] = max(
            scores.get(
                "inspect_pull_request_files",
                0,
            ),
            8,
        )

        matched[
            "inspect_pull_request_files"
        ] = list(
            dict.fromkeys(
                matched.get(
                    "inspect_pull_request_files",
                    [],
                )
                + [
                    phrase
                    for phrase in changed_file_phrases
                    if phrase in question
                ]
            )
        )

    # --------------------------------------------------------
    # PR diff.
    # --------------------------------------------------------

    if (
        "pr diff" in question
        or "pull request diff" in question
        or (
            (
                "what changed" in question
                or "show changes" in question
            )
            and (
                " pr" in question
                or "pull request" in question
            )
        )
    ):
        scores[
            "inspect_pull_request_diff"
        ] = max(
            scores.get(
                "inspect_pull_request_diff",
                0,
            ),
            8,
        )

        matched[
            "inspect_pull_request_diff"
        ] = list(
            dict.fromkeys(
                matched.get(
                    "inspect_pull_request_diff",
                    [],
                )
                + [
                    "pr diff context"
                ]
            )
        )

    # --------------------------------------------------------
    # Rerun means write operation, not inspection.
    # --------------------------------------------------------

    rerun_phrases = (
        "rerun",
        "retry",
        "run again",
    )

    if (
        any(
            _signal_matches(
                question,
                phrase,
            )
            for phrase in rerun_phrases
        )
        and (
            "job" in question
            or "github actions" in question
            or "actions job" in question
            or "workflow" in question
        )
    ):
        scores[
            "rerun_failed_job"
        ] = max(
            scores.get(
                "rerun_failed_job",
                0,
            ),
            9,
        )

        matched[
            "rerun_failed_job"
        ] = list(
            dict.fromkeys(
                matched.get(
                    "rerun_failed_job",
                    [],
                )
                + [
                    "rerun/retry job request"
                ]
            )
        )

    # --------------------------------------------------------
    # Review-thread inspection must beat resolve.
    #
    # This is important because:
    #
    #     "unresolved"
    #
    # contains the characters:
    #
    #     "resolve"
    #
    # We therefore use explicit inspection phrases first.
    # --------------------------------------------------------

    inspect_thread_phrases = (
        "inspect unresolved review threads",
        "show unresolved review threads",
        "list unresolved review threads",
        "inspect unresolved review comments",
        "show unresolved review comments",
        "list unresolved review comments",
        "inspect review threads",
        "inspect review thread",
        "show review threads",
        "list review threads",
        "review threads on my pr",
        "review comments on my pr",
        "review comments on this pr",
    )

    inspect_thread_matches = [
        phrase
        for phrase in inspect_thread_phrases
        if phrase in question
    ]

    if inspect_thread_matches:
        scores[
            "inspect_review_threads"
        ] = max(
            scores.get(
                "inspect_review_threads",
                0,
            ),
            9,
        )

        # Explicitly suppress accidental resolve routing.
        scores[
            "resolve_review_thread"
        ] = min(
            scores.get(
                "resolve_review_thread",
                0,
            ),
            0,
        )

        matched[
            "inspect_review_threads"
        ] = list(
            dict.fromkeys(
                matched.get(
                    "inspect_review_threads",
                    [],
                )
                + inspect_thread_matches
            )
        )

        matched[
            "resolve_review_thread"
        ] = []

    # --------------------------------------------------------
    # Resolve means modifying review state.
    #
    # Use complete phrases instead of:
    #
    #     "resolve" in question
    #
    # because "unresolved" contains "resolve".
    # --------------------------------------------------------

    resolve_phrases = (
        "resolve review thread",
        "resolve the review thread",
        "resolve review threads",
        "resolve this review thread",
        "mark review thread resolved",
        "mark this review thread resolved",
    )

    resolve_matches = [
        phrase
        for phrase in resolve_phrases
        if phrase in question
    ]

    if resolve_matches:
        scores[
            "resolve_review_thread"
        ] = max(
            scores.get(
                "resolve_review_thread",
                0,
            ),
            9,
        )

        matched[
            "resolve_review_thread"
        ] = list(
            dict.fromkeys(
                matched.get(
                    "resolve_review_thread",
                    [],
                )
                + resolve_matches
                + [
                    "resolve review thread context"
                ]
            )
        )


# ============================================================
# ROUTING
# ============================================================

def route_github_operation(
    question: str,
) -> GitHubRoute:
    """
    Determine the GitHub operation required for a request.

    This layer ONLY routes.

    It does not:
        - call GitHub
        - modify repositories
        - execute commands
        - create commits
        - create pull requests

    Execution belongs to Falcon's GitHub/tool execution layer.
    """

    normalized = _normalize_question(
        question
    )

    if not normalized:
        return GitHubRoute(
            operation="inspect_repository",
            confidence=0.0,
            metadata={
                "reason": "empty_question",
            },
        )

    scores: dict[str, int] = {}
    matched: dict[str, list[str]] = {}

    for operation in GITHUB_OPERATIONS:
        score, signals = _score_operation(
            normalized,
            operation,
        )

        scores[
            operation
        ] = score

        matched[
            operation
        ] = signals

    _apply_special_cases(
        normalized,
        scores,
        matched,
    )

    # --------------------------------------------------------
    # Rank operations.
    # --------------------------------------------------------

    ranked = sorted(
        GITHUB_OPERATIONS.keys(),
        key=lambda operation: (
            scores.get(
                operation,
                0,
            ),
            GITHUB_OPERATIONS[
                operation
            ].get(
                "priority",
                0,
            ),
        ),
        reverse=True,
    )

    best_operation = ranked[0]

    best_score = scores.get(
        best_operation,
        0,
    )

    # --------------------------------------------------------
    # No recognized operation.
    # --------------------------------------------------------

    if best_score <= 0:
        return GitHubRoute(
            operation="inspect_repository",
            confidence=0.25,
            requires_write_permission=False,
            requires_approval=False,
            matched_signals=[],
            metadata={
                "reason": (
                    "no_specific_github_operation_detected"
                ),
                "question": normalized,
                "scores": scores,
            },
        )

    # --------------------------------------------------------
    # Confidence.
    # --------------------------------------------------------

    if best_score >= 8:
        confidence = 0.95
    elif best_score >= 5:
        confidence = 0.90
    elif best_score >= 3:
        confidence = 0.85
    elif best_score >= 2:
        confidence = 0.80
    else:
        confidence = 0.65

    # --------------------------------------------------------
    # Find second-best score.
    # --------------------------------------------------------

    second_score = 0

    for operation in ranked:
        if operation == best_operation:
            continue

        second_score = scores.get(
            operation,
            0,
        )
        break

    # --------------------------------------------------------
    # Ambiguous close competition.
    # --------------------------------------------------------

    if (
        second_score > 0
        and second_score >= best_score
    ):
        confidence -= 0.15

    confidence = max(
        0.0,
        min(
            1.0,
            confidence,
        ),
    )

    definition = GITHUB_OPERATIONS[
        best_operation
    ]

    route = GitHubRoute(
        operation=best_operation,
        confidence=round(
            confidence,
            4,
        ),
        requires_write_permission=bool(
            definition.get(
                "write",
                False,
            )
        ),
        requires_approval=bool(
            definition.get(
                "approval",
                False,
            )
        ),
        matched_signals=matched.get(
            best_operation,
            [],
        ),
        metadata={
            "question": normalized,
            "score": best_score,
            "scores": scores,
            "operation_description": definition.get(
                "description"
            ),
            "operation_priority": definition.get(
                "priority"
            ),
        },
    )

    logger.info(
        "GitHub route: operation=%s confidence=%.2f",
        route.operation,
        route.confidence,
    )

    return route


# ============================================================
# PUBLIC HELPERS
# ============================================================

def github_requires_write(
    question: str,
) -> bool:
    return route_github_operation(
        question
    ).requires_write_permission


def github_requires_approval(
    question: str,
) -> bool:
    return route_github_operation(
        question
    ).requires_approval


def github_operation(
    question: str,
) -> str:
    return route_github_operation(
        question
    ).operation


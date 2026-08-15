"""
Falcon AI - GitHub Execution Layer

Complete GitHub execution pipeline:

    Natural Language
          |
          v
    GitHub Router
          |
          v
    Parameter Extraction
          |
          v
    Permission Check
          |
          v
    Approval Check
          |
          v
    Parameter Validation
          |
          v
    GitHub Client
          |
          v
    Structured Result

Supports:

    Repository inspection
    Files
    Branches
    Commits
    Pull requests
    PR files
    PR diffs
    PR reviews
    Review threads
    Issues
    GitHub Actions
    Code search

The real client lives in github_client.py.

The MockGitHubClient remains available for safe local tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from app.agents.github_capability import (
    GITHUB_OPERATIONS,
    GitHubRoute,
    route_github_operation,
)


# ============================================================================
# RESULT
# ============================================================================


@dataclass
class GitHubExecutionResult:
    success: bool
    operation: str
    message: str

    data: Any = None

    confidence: float = 0.0

    requires_write_permission: bool = False
    requires_approval: bool = False

    approval_required: bool = False
    executed: bool = False

    error: Optional[str] = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:

        return {
            "success": self.success,
            "operation": self.operation,
            "message": self.message,
            "data": self.data,
            "confidence": self.confidence,
            "requires_write_permission":
                self.requires_write_permission,
            "requires_approval":
                self.requires_approval,
            "approval_required":
                self.approval_required,
            "executed":
                self.executed,
            "error":
                self.error,
            "metadata":
                self.metadata,
        }


# ============================================================================
# CLIENT PROTOCOL
# ============================================================================


class GitHubClientProtocol(Protocol):

    def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> Any:
        ...


# ============================================================================
# MOCK CLIENT
# ============================================================================


class MockGitHubClient:

    def __init__(self) -> None:

        self.calls: list[
            dict[str, Any]
        ] = []

    def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        call = {
            "operation": operation,
            "parameters": dict(
                parameters
            ),
        }

        self.calls.append(call)

        return {
            "mock": True,
            "operation": operation,
            "parameters": dict(
                parameters
            ),
            "message": (
                f"Mock GitHub operation "
                f"'{operation}' executed."
            ),
        }


# ============================================================================
# PERMISSIONS
# ============================================================================


@dataclass
class GitHubPermissionState:

    read_permission: bool = True

    write_permission: bool = False

    approval_granted: bool = False


_DEFAULT_PERMISSIONS = GitHubPermissionState()


# ============================================================================
# NORMALIZATION
# ============================================================================


def _normalize_question(
    question: str,
) -> str:

    return " ".join(
        question.strip().split()
    )


# ============================================================================
# INTEGER EXTRACTION
# ============================================================================


def _extract_positive_int(
    question: str,
    patterns: list[str],
) -> Optional[int]:

    for pattern in patterns:

        match = re.search(
            pattern,
            question,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        try:

            value = int(
                match.group(1)
            )

            if value > 0:
                return value

        except (
            TypeError,
            ValueError,
        ):
            continue

    return None


# ============================================================================
# PULL REQUEST NUMBER
# ============================================================================


def _extract_pull_request_number(
    question: str,
) -> Optional[int]:

    patterns = [

        # PR diff/files/reviews/threads #42
        r"\bpr\s+(?:diff|files?|reviews?|review|threads?|thread)\s*#?\s*(\d+)\b",

        # PR #42
        r"\bpr\s*#\s*(\d+)\b",

        # PR 42
        r"\bpr\s+(\d+)\b",

        # pull request #42
        r"\bpull[\s-]*request\s*#\s*(\d+)\b",

        # pull request 42
        r"\bpull[\s-]*request\s+(\d+)\b",

        # pull request number 42
        r"\bpull[\s-]*request\s+number\s*#?\s*(\d+)\b",

        # PR number 42
        r"\bpr\s+number\s*#?\s*(\d+)\b",

        # pull-request #42
        r"\bpull[\s-]*request\s*#?\s*(\d+)\b",
    ]

    return _extract_positive_int(
        question,
        patterns,
    )


# ============================================================================
# ISSUE NUMBER
# ============================================================================


def _extract_issue_number(
    question: str,
) -> Optional[int]:

    patterns = [

        r"\bissue\s*#\s*(\d+)\b",

        r"\bissue\s+(\d+)\b",

        r"\bissue\s+number\s*#?\s*(\d+)\b",
    ]

    return _extract_positive_int(
        question,
        patterns,
    )


# ============================================================================
# JOB NUMBER
# ============================================================================


def _extract_job_number(
    question: str,
) -> Optional[int]:

    patterns = [

        r"\bjob\s*#\s*(\d+)\b",

        r"\bjob\s+(\d+)\b",

        r"\bjob\s+number\s*#?\s*(\d+)\b",

        r"\brun\s*#\s*(\d+)\b",

        r"\brun\s+(\d+)\b",

        r"\brun\s+number\s*#?\s*(\d+)\b",
    ]

    return _extract_positive_int(
        question,
        patterns,
    )


# ============================================================================
# COMMIT SHA
# ============================================================================


def _extract_commit_sha(
    question: str,
) -> Optional[str]:

    match = re.search(
        r"\b[0-9a-f]{7,40}\b",
        question,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(0)

    return None


# ============================================================================
# FILE / GENERIC PARAMETER HELPERS
# ============================================================================

def _extract_file_path(question: str) -> Optional[str]:
    patterns=[
        r"\bfile\s+[`\"]?([A-Za-z0-9._/\-]+)[`\"]?",
        r"\bread\s+(?:the\s+)?[`\"]?([A-Za-z0-9._/\-]+)[`\"]?",
        r"\bopen\s+[`\"]?([A-Za-z0-9._/\-]+)[`\"]?",
        r"\binspect\s+file\s+[`\"]?([A-Za-z0-9._/\-]+)[`\"]?",
    ]
    for pattern in patterns:
        m=re.search(pattern,question,flags=re.IGNORECASE)
        if m and m.group(1).lower() not in {"the","a","an","my","this","github"}: return m.group(1)
    if re.search(r"\bread\s+(?:the\s+)?readme(?:\s+file)?\b",question,flags=re.IGNORECASE): return "README.md"
    return None

def _extract_after_keyword(question: str, keywords: list[str]) -> Optional[str]:
    for keyword in sorted(keywords,key=len,reverse=True):
        m=re.search(r"\b"+re.escape(keyword)+r"\b\s*(?:for|:)?\s*(.+)$",question,flags=re.IGNORECASE)
        if m:
            value=m.group(1).strip().strip('`\"\'')
            value=re.sub(r"\b(?:in|on)\s+(?:pr|pull request)\s*#?\d+\b.*$","",value,flags=re.IGNORECASE).strip()
            if value:return value
    return None

def _extract_pr_parameters(question: str) -> dict[str,Any]:
    out:{} = {}
    title=re.search(r"\b(?:title|called|named)\s+[`\"]([^`\"]+)[`\"]",question,flags=re.IGNORECASE)
    if title: out["title"]=title.group(1).strip()
    head=re.search(r"\b(?:from|head|source branch)\s+([A-Za-z0-9._/\-]+)",question,flags=re.IGNORECASE)
    if head: out["head"]=head.group(1)
    base=re.search(r"\b(?:into|base|target branch)\s+([A-Za-z0-9._/\-]+)",question,flags=re.IGNORECASE)
    if base: out["base"]=base.group(1)
    body=re.search(r"\bbody\s*:\s*(.+)$",question,flags=re.IGNORECASE)
    if body: out["body"]=body.group(1).strip()
    return out


# ============================================================================
# BRANCH
# ============================================================================


def _extract_branch_name(
    question: str,
) -> Optional[str]:

    patterns = [

        r"\bbranch\s+(?:called|named)\s+([A-Za-z0-9._/\-]+)",

        r"\bcreate\s+(?:a\s+)?(?:new\s+)?branch\s+([A-Za-z0-9._/\-]+)",

        r"\bbranch\s*:\s*([A-Za-z0-9._/\-]+)",

        r"\binspect\s+branch\s+([A-Za-z0-9._/\-]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            question,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


# ============================================================================
# REPOSITORY
# ============================================================================


def _extract_repository(
    question: str,
) -> Optional[str]:
    """Extract an explicit owner/repository without mistaking file paths for repos."""
    explicit = re.search(
        r"\b(?:repo|repository)\s+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b",
        question, flags=re.IGNORECASE,
    )
    if explicit:
        return explicit.group(1)
    # Only accept a slash pair that looks like owner/repo and is not a file path.
    for match in re.finditer(r"\b([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)\b", question):
        candidate = match.group(0)
        if candidate.lower().endswith((".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml")):
            continue
        if "file" in question[:match.start()].lower() or "read" in question[:match.start()].lower():
            continue
        return candidate
    return None


def _extract_base_parameters(
    question: str,
) -> dict[str, Any]:

    parameters: dict[str, Any] = {}

    repository = _extract_repository(
        question
    )

    if repository:
        parameters[
            "repository"
        ] = repository

    pull_request_number = (
        _extract_pull_request_number(
            question
        )
    )

    if pull_request_number is not None:

        parameters[
            "pull_request_number"
        ] = pull_request_number

    issue_number = (
        _extract_issue_number(
            question
        )
    )

    if issue_number is not None:

        parameters[
            "issue_number"
        ] = issue_number

    job_number = (
        _extract_job_number(
            question
        )
    )

    if job_number is not None:

        parameters[
            "job_number"
        ] = job_number

    commit_sha = (
        _extract_commit_sha(
            question
        )
    )

    if commit_sha:

        parameters[
            "commit_sha"
        ] = commit_sha

    branch_name = (
        _extract_branch_name(
            question
        )
    )

    if branch_name:

        parameters[
            "branch"
        ] = branch_name

    file_path = (
        _extract_file_path(
            question
        )
    )

    if file_path:

        parameters[
            "file_path"
        ] = file_path

    return parameters


# ============================================================================
# REQUIRED PARAMETERS
# ============================================================================


OPERATION_REQUIRED_PARAMETERS: dict[
    str,
    list[str],
] = {

    "read_pull_request": [
        "pull_request_number",
    ],

    "inspect_pull_request_files": [
        "pull_request_number",
    ],

    "inspect_pull_request_diff": [
        "pull_request_number",
    ],

    "inspect_review_threads": [
        "pull_request_number",
    ],

    "resolve_review_thread": [
        "pull_request_number",
    ],

    "inspect_pull_request_reviews": [
        "pull_request_number",
    ],

    "create_pull_request": [
        "title",
        "head",
    ],

    "create_branch": [
        "branch",
    ],

    "inspect_branch": [
        "branch",
    ],

    "read_file": [
        "file_path",
    ],

    "update_file": [
        "file_path",
        "content",
    ],

    "delete_file": [
        "file_path",
    ],

    "create_file": [
        "file_path",
        "content",
    ],

    "read_issue": [
        "issue_number",
    ],

    "update_issue": [
        "issue_number",
    ],

    "create_issue": [
        "title",
    ],

    "inspect_job": [
        "job_number",
    ],

    "inspect_commit": [
        "commit_sha",
    ],

    "inspect_workflow": [
        "workflow",
    ],

    "search_code": [
        "query",
    ],
}


# ============================================================================
# PARAMETER EXTRACTION
# ============================================================================


def extract_github_parameters(
    question: str,
    operation: str,
) -> dict[str, Any]:

    normalized = _normalize_question(
        question
    )

    parameters = _extract_base_parameters(
        normalized
    )

    # --------------------------------------------------------------
    # PR PARAMETERS
    # --------------------------------------------------------------

    if operation == "create_pull_request":

        parameters.update(
            _extract_pr_parameters(
                normalized
            )
        )

    # --------------------------------------------------------------
    # README
    # --------------------------------------------------------------

    if operation == "read_file":

        if re.search(
            r"\bread\s+(?:the\s+)?readme(?:\s+file)?\b",
            normalized,
            flags=re.IGNORECASE,
        ):
            parameters[
                "file_path"
            ] = "README.md"

    # --------------------------------------------------------------
    # MAIN BRANCH
    # --------------------------------------------------------------

    if operation == "inspect_branch":

        if "branch" not in parameters:

            if re.search(
                r"\bmain\s+branch\b|\bmain\b",
                normalized,
                flags=re.IGNORECASE,
            ):
                parameters[
                    "branch"
                ] = "main"

            elif re.search(
                r"\bmaster\s+branch\b|\bmaster\b",
                normalized,
                flags=re.IGNORECASE,
            ):
                parameters[
                    "branch"
                ] = "master"

    # --------------------------------------------------------------
    # WORKFLOW
    # --------------------------------------------------------------

    if operation == "inspect_workflow":

        workflow = _extract_after_keyword(
            normalized,
            ["workflow"],
        )

        if workflow:
            parameters[
                "workflow"
            ] = workflow

    # --------------------------------------------------------------
    # CODE SEARCH
    # --------------------------------------------------------------

    if operation == "search_code":

        query = _extract_after_keyword(
            normalized,
            [
                "search code",
                "search",
                "find code",
            ],
        )

        if query:
            parameters[
                "query"
            ] = query

    return parameters


# ============================================================================
# MISSING PARAMETER
# ============================================================================


def _find_missing_parameters(
    operation: str,
    parameters: dict[str, Any],
) -> list[str]:

    required = (
        OPERATION_REQUIRED_PARAMETERS.get(
            operation,
            [],
        )
    )

    return [
        parameter
        for parameter in required
        if parameter not in parameters
        or parameters[parameter]
        in (
            None,
            "",
        )
    ]


def _missing_parameter_message(
    operation: str,
    missing: list[str],
) -> str:

    labels = {

        "pull_request_number":
            "the pull request number",

        "issue_number":
            "the issue number",

        "job_number":
            "the GitHub Actions job/run number",

        "commit_sha":
            "the commit SHA",

        "branch":
            "the branch name",

        "file_path":
            "the repository file path",

        "content":
            "the file content",

        "title":
            "the title",

        "head":
            "the source branch",

        "workflow":
            "the workflow",

        "query":
            "the search query",
    }

    readable = [
        labels.get(
            parameter,
            parameter,
        )
        for parameter in missing
    ]

    if len(readable) == 1:

        return (
            f"I need {readable[0]} before "
            f"I can execute GitHub operation "
            f"'{operation}'."
        )

    return (
        f"I need {', '.join(readable[:-1])}, "
        f"and {readable[-1]} before I can "
        f"execute GitHub operation "
        f"'{operation}'."
    )


# ============================================================================
# EXECUTION
# ============================================================================


def execute_github_operation(
    question: str,
    *,
    client: Optional[
        GitHubClientProtocol
    ] = None,
    permissions: Optional[
        GitHubPermissionState
    ] = None,
    parameters: Optional[
        dict[str, Any]
    ] = None,
) -> GitHubExecutionResult:

    permissions = (
        permissions
        or _DEFAULT_PERMISSIONS
    )

    route: GitHubRoute = (
        route_github_operation(
            question
        )
    )

    operation = route.operation

    # --------------------------------------------------------------
    # UNKNOWN OPERATION
    # --------------------------------------------------------------

    if operation not in GITHUB_OPERATIONS:

        return GitHubExecutionResult(

            success=False,

            operation=operation,

            message=(
                "Falcon could not determine "
                "a supported GitHub operation."
            ),

            confidence=route.confidence,

            error=(
                "unsupported_github_operation"
            ),

            metadata={
                "route":
                    route.to_dict(),

                "question":
                    question,
            },
        )

    # --------------------------------------------------------------
    # READ PERMISSION
    # --------------------------------------------------------------

    if not route.requires_write_permission:

        if not permissions.read_permission:

            return GitHubExecutionResult(

                success=False,

                operation=operation,

                message=(
                    "Falcon does not currently "
                    "have GitHub read permission."
                ),

                confidence=route.confidence,

                error=(
                    "read_permission_required"
                ),

                metadata={
                    "route":
                        route.to_dict(),

                    "question":
                        question,
                },
            )

    # --------------------------------------------------------------
    # WRITE PERMISSION
    # --------------------------------------------------------------

    if route.requires_write_permission:

        if not permissions.write_permission:

            return GitHubExecutionResult(

                success=False,

                operation=operation,

                message=(
                    "This GitHub operation requires "
                    "write permission. Falcon has not "
                    "been granted write permission."
                ),

                confidence=route.confidence,

                requires_write_permission=True,

                requires_approval=(
                    route.requires_approval
                ),

                approval_required=False,

                executed=False,

                error=(
                    "write_permission_required"
                ),

                metadata={
                    "route":
                        route.to_dict(),

                    "question":
                        question,
                },
            )

    # --------------------------------------------------------------
    # APPROVAL
    # --------------------------------------------------------------

    if route.requires_approval:

        if not permissions.approval_granted:

            return GitHubExecutionResult(

                success=False,

                operation=operation,

                message=(
                    f"GitHub operation "
                    f"'{operation}' requires "
                    "user approval before execution."
                ),

                confidence=route.confidence,

                requires_write_permission=(
                    route.requires_write_permission
                ),

                requires_approval=True,

                approval_required=True,

                executed=False,

                error="approval_required",

                metadata={
                    "route":
                        route.to_dict(),

                    "question":
                        question,
                },
            )

    # --------------------------------------------------------------
    # PARAMETERS
    # --------------------------------------------------------------

    extracted_parameters = (
        extract_github_parameters(
            question,
            operation,
        )
    )

    if parameters:

        extracted_parameters.update(
            parameters
        )

    # --------------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------------

    missing = (
        _find_missing_parameters(
            operation,
            extracted_parameters,
        )
    )

    if missing:

        return GitHubExecutionResult(

            success=False,

            operation=operation,

            message=(
                _missing_parameter_message(
                    operation,
                    missing,
                )
            ),

            confidence=route.confidence,

            requires_write_permission=(
                route.requires_write_permission
            ),

            requires_approval=(
                route.requires_approval
            ),

            approval_required=False,

            executed=False,

            error=(
                "missing_required_parameter"
            ),

            metadata={
                "route":
                    route.to_dict(),

                "question":
                    question,

                "parameters":
                    extracted_parameters,

                "missing_parameters":
                    missing,
            },
        )

    # --------------------------------------------------------------
    # CLIENT
    # --------------------------------------------------------------

    if client is None:

        return GitHubExecutionResult(

            success=False,

            operation=operation,

            message=(
                "GitHub operation was routed "
                "successfully, but no GitHub "
                "execution client has been configured."
            ),

            confidence=route.confidence,

            requires_write_permission=(
                route.requires_write_permission
            ),

            requires_approval=(
                route.requires_approval
            ),

            approval_required=False,

            executed=False,

            error=(
                "github_client_not_configured"
            ),

            metadata={
                "route":
                    route.to_dict(),

                "question":
                    question,

                "parameters":
                    extracted_parameters,
            },
        )

    # --------------------------------------------------------------
    # EXECUTION
    # --------------------------------------------------------------

    try:

        data = client.execute(
            operation,
            extracted_parameters,
        )

        return GitHubExecutionResult(

            success=True,

            operation=operation,

            message=(
                f"GitHub operation "
                f"'{operation}' executed successfully."
            ),

            data=data,

            confidence=route.confidence,

            requires_write_permission=(
                route.requires_write_permission
            ),

            requires_approval=(
                route.requires_approval
            ),

            approval_required=False,

            executed=True,

            error=None,

            metadata={
                "route":
                    route.to_dict(),

                "question":
                    question,

                "parameters":
                    extracted_parameters,
            },
        )

    except Exception as exc:

        return GitHubExecutionResult(

            success=False,

            operation=operation,

            message=(
                f"GitHub operation "
                f"'{operation}' failed during execution."
            ),

            data=None,

            confidence=route.confidence,

            requires_write_permission=(
                route.requires_write_permission
            ),

            requires_approval=(
                route.requires_approval
            ),

            approval_required=False,

            executed=False,

            error=str(exc),

            metadata={
                "route":
                    route.to_dict(),

                "question":
                    question,

                "parameters":
                    extracted_parameters,
            },
        )


# ============================================================================
# REAL CLIENT FACTORY
# ============================================================================


def create_github_client():

    from app.agents.github_client import (
        PyGithubGitHubClient,
    )

    return PyGithubGitHubClient()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


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


# ============================================================================
# LOCAL TESTING
# ============================================================================


if __name__ == "__main__":

    client = MockGitHubClient()

    tests = [

        "inspect my GitHub pull request #42",

        "show me the files changed in PR #42",

        "show me the PR diff #42",

        "inspect unresolved review threads in PR #42",

        "read the README file",

        "read the file app/agents/github_executor.py",

        "inspect branch main",

        "inspect commit abcdef1234567",

        "inspect issue #17",

        "inspect job #55",

        "create a new branch feature/github-execution",
    ]

    print()
    print("=" * 80)
    print("FALCON GITHUB EXECUTION TEST")
    print("=" * 80)

    for question in tests:

        print()
        print("QUESTION:")
        print(question)

        result = execute_github_operation(
            question,
            client=client,
        )

        print()
        print("RESULT:")
        print(result.to_dict())

    print()
    print("=" * 80)
    print("MOCK CALLS")
    print("=" * 80)

    for call in client.calls:

        print(call)
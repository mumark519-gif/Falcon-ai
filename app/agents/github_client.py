"""
Falcon AI - GitHub Client
=========================

Complete GitHub execution client for Falcon AI.

Responsibilities
----------------
- Authenticate with GitHub using FALCON_GITHUB_TOKEN / GITHUB_TOKEN.
- Execute the GitHub operations routed by github_capability.py.
- Support repository, file, branch, commit, PR, review, issue,
  Actions, search and write operations.
- Keep the GitHub API implementation isolated from Falcon's routing layer.
- Return normalized Python dictionaries.
- Never print or expose the GitHub token.
- Support repository discovery from:
    1. Explicit operation parameter.
    2. FALCON_GITHUB_REPOSITORY.
    3. GITHUB_REPOSITORY.
    4. GitHub Actions GITHUB_REPOSITORY.
- Support GitHub Enterprise through GITHUB_API_URL.
- Use GitHub REST API v3.

This file intentionally does not perform tests automatically.

Required environment variables
-------------------------------
FALCON_GITHUB_TOKEN=github_pat_...
or
GITHUB_TOKEN=github_pat_...

Optional:
FALCON_GITHUB_REPOSITORY=owner/repository
GITHUB_REPOSITORY=owner/repository
GITHUB_API_URL=https://api.github.com

Examples
--------
from app.agents.github_client import GitHubClient

client = GitHubClient()

client.execute(
    "read_pull_request",
    {
        "repository": "owner/repository",
        "pull_request_number": 42,
    },
)

client.execute(
    "read_file",
    {
        "repository": "owner/repository",
        "file_path": "README.md",
    },
)
"""

from __future__ import annotations

import base64
import os
from typing import Any, Optional
from urllib.parse import quote, urlparse

import requests


# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_GITHUB_API_URL = "https://api.github.com"

DEFAULT_TIMEOUT = 30

API_VERSION = "2022-11-28"


# ============================================================================
# EXCEPTIONS
# ============================================================================


class GitHubClientError(Exception):
    """Base GitHub client error."""


class GitHubAuthenticationError(GitHubClientError):
    """Authentication failed."""


class GitHubPermissionError(GitHubClientError):
    """GitHub permission error."""


class GitHubNotFoundError(GitHubClientError):
    """GitHub resource was not found."""


class GitHubValidationError(GitHubClientError):
    """Invalid GitHub request."""


class GitHubRateLimitError(GitHubClientError):
    """GitHub API rate limit was reached."""


class GitHubAPIError(GitHubClientError):
    """Generic GitHub API error."""


# ============================================================================
# SMALL HELPERS
# ============================================================================


def _clean(value: Any) -> Any:
    """
    Remove unnecessary None values recursively.
    """

    if isinstance(value, dict):
        return {
            key: _clean(item)
            for key, item in value.items()
            if item is not None
        }

    if isinstance(value, list):
        return [_clean(item) for item in value]

    return value


def _require_positive_int(
    parameters: dict[str, Any],
    name: str,
) -> int:
    """
    Read a required positive integer.
    """

    value = parameters.get(name)

    if value is None:
        raise GitHubValidationError(
            f"Missing required GitHub parameter: {name}"
        )

    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise GitHubValidationError(
            f"GitHub parameter '{name}' must be an integer."
        ) from exc

    if value <= 0:
        raise GitHubValidationError(
            f"GitHub parameter '{name}' must be greater than zero."
        )

    return value


def _require_string(
    parameters: dict[str, Any],
    name: str,
) -> str:
    """
    Read a required non-empty string.
    """

    value = parameters.get(name)

    if value is None:
        raise GitHubValidationError(
            f"Missing required GitHub parameter: {name}"
        )

    value = str(value).strip()

    if not value:
        raise GitHubValidationError(
            f"GitHub parameter '{name}' cannot be empty."
        )

    return value


def _optional_string(
    parameters: dict[str, Any],
    name: str,
) -> Optional[str]:
    value = parameters.get(name)

    if value is None:
        return None

    value = str(value).strip()

    return value or None


def _encode_path(path: str) -> str:
    """
    Encode a repository path while preserving '/' separators.
    """

    return quote(path.strip("/"), safe="/._-")


def _encode_branch(branch: str) -> str:
    return quote(branch, safe="/._-")


def _encode_sha(sha: str) -> str:
    return quote(sha, safe="")


def _encode_query(value: str) -> str:
    return quote(value, safe="")


def _parse_repository(value: str) -> tuple[str, str]:
    """
    Convert:

        owner/repository

    into:

        ("owner", "repository")

    Also accepts:

        https://github.com/owner/repository
        git@github.com:owner/repository.git
    """

    value = value.strip()

    if not value:
        raise GitHubValidationError(
            "GitHub repository cannot be empty."
        )

    # HTTPS / HTTP GitHub URL.
    if value.startswith("http://") or value.startswith("https://"):

        parsed = urlparse(value)

        path = parsed.path.strip("/")

        parts = path.split("/")

        if len(parts) >= 2:

            owner = parts[0]

            repository = parts[1]

            repository = repository.removesuffix(".git")

            return owner, repository

    # SSH GitHub URL.
    if value.startswith("git@github.com:"):

        value = value.split(":", 1)[1]

        value = value.removesuffix(".git")

    # Normal owner/repository.
    parts = value.strip("/").split("/")

    if len(parts) != 2:

        raise GitHubValidationError(
            "GitHub repository must use owner/repository format."
        )

    owner = parts[0].strip()

    repository = parts[1].strip()

    if not owner or not repository:

        raise GitHubValidationError(
            "GitHub repository must use owner/repository format."
        )

    return owner, repository


# ============================================================================
# GITHUB CLIENT
# ============================================================================


class GitHubClient:
    """
    Complete GitHub REST API client for Falcon AI.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        repository: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:

        self.token = (
            token
            or os.getenv("FALCON_GITHUB_TOKEN")
            or os.getenv("GITHUB_TOKEN")
        )

        self.repository = (
            repository
            or os.getenv("FALCON_GITHUB_REPOSITORY")
            or os.getenv("GITHUB_REPOSITORY")
        )

        self.api_url = (
            api_url
            or os.getenv("GITHUB_API_URL")
            or DEFAULT_GITHUB_API_URL
        ).rstrip("/")

        self.timeout = timeout

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "Falcon-AI-GitHub-Client",
            }
        )

        if self.token:

            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.token}",
                }
            )

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------

    def _require_token(self) -> None:

        if not self.token:

            raise GitHubAuthenticationError(
                "GitHub token is not configured. "
                "Set FALCON_GITHUB_TOKEN or GITHUB_TOKEN."
            )

    def get_authenticated_user(self) -> dict[str, Any]:

        self._require_token()

        return self._request(
            "GET",
            "/user",
        )

    # ------------------------------------------------------------------
    # REPOSITORY
    # ------------------------------------------------------------------

    def _resolve_repository(
        self,
        parameters: dict[str, Any],
    ) -> tuple[str, str]:

        repository = (
            parameters.get("repository")
            or parameters.get("repo")
            or self.repository
        )

        if not repository:

            raise GitHubValidationError(
                "GitHub repository is required. "
                "Provide repository='owner/repository' "
                "or configure FALCON_GITHUB_REPOSITORY."
            )

        return _parse_repository(str(repository))

    def _repo_path(
        self,
        owner: str,
        repository: str,
        suffix: str = "",
    ) -> str:

        base = (
            f"/repos/"
            f"{quote(owner, safe='')}/"
            f"{quote(repository, safe='')}"
        )

        if suffix:

            if not suffix.startswith("/"):
                suffix = "/" + suffix

            base += suffix

        return base

    def get_repository(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        return self._request(
            "GET",
            self._repo_path(owner, repository),
        )

    def get_repository_branches(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        query = self._pagination_parameters(parameters)

        data = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                "/branches",
            ),
            params=query,
        )

        return {
            "repository": f"{owner}/{repository}",
            "branches": data,
        }

    # ------------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------------

    def _pagination_parameters(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        result: dict[str, Any] = {}

        per_page = parameters.get("per_page")

        page = parameters.get("page")

        if per_page is not None:

            try:
                per_page = int(per_page)
            except (TypeError, ValueError) as exc:

                raise GitHubValidationError(
                    "per_page must be an integer."
                ) from exc

            per_page = max(1, min(per_page, 100))

            result["per_page"] = per_page

        if page is not None:

            try:
                page = int(page)
            except (TypeError, ValueError) as exc:

                raise GitHubValidationError(
                    "page must be an integer."
                ) from exc

            page = max(1, page)

            result["page"] = page

        return result

    # ------------------------------------------------------------------
    # FILES
    # ------------------------------------------------------------------

    def read_file(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        file_path = _require_string(
            parameters,
            "file_path",
        )

        ref = _optional_string(
            parameters,
            "ref",
        )

        endpoint = self._repo_path(
            owner,
            repository,
            f"/contents/{_encode_path(file_path)}",
        )

        params = {}

        if ref:
            params["ref"] = ref

        data = self._request(
            "GET",
            endpoint,
            params=params,
        )

        # GitHub returns a list for directories.
        if isinstance(data, list):

            return {
                "repository": f"{owner}/{repository}",
                "path": file_path,
                "type": "directory",
                "items": data,
            }

        content = data.get("content")

        decoded_content = None

        if content:

            try:

                decoded_content = base64.b64decode(
                    content
                ).decode(
                    "utf-8",
                    errors="replace",
                )

            except Exception:

                decoded_content = None

        return {
            "repository": f"{owner}/{repository}",
            "path": file_path,
            "name": data.get("name"),
            "sha": data.get("sha"),
            "size": data.get("size"),
            "type": data.get("type"),
            "encoding": data.get("encoding"),
            "content": decoded_content,
            "download_url": data.get("download_url"),
            "html_url": data.get("html_url"),
        }

    def create_file(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        file_path = _require_string(
            parameters,
            "file_path",
        )

        content = parameters.get("content")

        if content is None:

            raise GitHubValidationError(
                "Missing required GitHub parameter: content"
            )

        message = (
            parameters.get("commit_message")
            or parameters.get("message")
            or f"Create {file_path}"
        )

        branch = _optional_string(
            parameters,
            "branch",
        )

        body: dict[str, Any] = {
            "message": str(message),
            "content": base64.b64encode(
                str(content).encode("utf-8")
            ).decode("ascii"),
        }

        if branch:

            body["branch"] = branch

        return self._request(
            "PUT",
            self._repo_path(
                owner,
                repository,
                f"/contents/{_encode_path(file_path)}",
            ),
            json=body,
        )

    def update_file(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        file_path = _require_string(
            parameters,
            "file_path",
        )

        content = parameters.get("content")

        if content is None:

            raise GitHubValidationError(
                "Missing required GitHub parameter: content"
            )

        message = (
            parameters.get("commit_message")
            or parameters.get("message")
            or f"Update {file_path}"
        )

        branch = _optional_string(
            parameters,
            "branch",
        )

        sha = _optional_string(
            parameters,
            "sha",
        )

        # If SHA was not explicitly supplied, obtain the current file SHA.
        if not sha:

            existing = self.read_file(
                {
                    "repository": f"{owner}/{repository}",
                    "file_path": file_path,
                    "ref": branch,
                }
            )

            sha = existing.get("sha")

        if not sha:

            raise GitHubValidationError(
                "GitHub file SHA is required to update the file."
            )

        body: dict[str, Any] = {
            "message": str(message),
            "content": base64.b64encode(
                str(content).encode("utf-8")
            ).decode("ascii"),
            "sha": sha,
        }

        if branch:

            body["branch"] = branch

        return self._request(
            "PUT",
            self._repo_path(
                owner,
                repository,
                f"/contents/{_encode_path(file_path)}",
            ),
            json=body,
        )

    def delete_file(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        file_path = _require_string(
            parameters,
            "file_path",
        )

        message = (
            parameters.get("commit_message")
            or parameters.get("message")
            or f"Delete {file_path}"
        )

        branch = _optional_string(
            parameters,
            "branch",
        )

        sha = _optional_string(
            parameters,
            "sha",
        )

        if not sha:

            existing = self.read_file(
                {
                    "repository": f"{owner}/{repository}",
                    "file_path": file_path,
                    "ref": branch,
                }
            )

            sha = existing.get("sha")

        if not sha:

            raise GitHubValidationError(
                "GitHub file SHA is required to delete the file."
            )

        body: dict[str, Any] = {
            "message": str(message),
            "sha": sha,
        }

        if branch:

            body["branch"] = branch

        return self._request(
            "DELETE",
            self._repo_path(
                owner,
                repository,
                f"/contents/{_encode_path(file_path)}",
            ),
            json=body,
        )

    # ------------------------------------------------------------------
    # BRANCHES
    # ------------------------------------------------------------------

    def inspect_branch(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        branch = _require_string(
            parameters,
            "branch",
        )

        return self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/branches/{_encode_branch(branch)}",
            ),
        )

    def create_branch(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        branch = _require_string(
            parameters,
            "branch",
        )

        source = (
            _optional_string(parameters, "source")
            or _optional_string(parameters, "from_branch")
            or "main"
        )

        source_data = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/git/ref/heads/{_encode_branch(source)}",
            ),
        )

        sha = (
            source_data
            .get("object", {})
            .get("sha")
        )

        if not sha:

            raise GitHubAPIError(
                "Could not determine source branch SHA."
            )

        return self._request(
            "POST",
            self._repo_path(
                owner,
                repository,
                "/git/refs",
            ),
            json={
                "ref": f"refs/heads/{branch}",
                "sha": sha,
            },
        )

    # ------------------------------------------------------------------
    # COMMITS
    # ------------------------------------------------------------------

    def inspect_commit(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        sha = _require_string(
            parameters,
            "commit_sha",
        )

        return self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/commits/{_encode_sha(sha)}",
            ),
        )

    def list_commits(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        params = self._pagination_parameters(parameters)

        branch = _optional_string(
            parameters,
            "branch",
        )

        if branch:

            params["sha"] = branch

        data = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                "/commits",
            ),
            params=params,
        )

        return {
            "repository": f"{owner}/{repository}",
            "commits": data,
        }

    def compare_commits(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        base = (
            _optional_string(parameters, "base")
            or _optional_string(parameters, "base_sha")
        )

        head = (
            _optional_string(parameters, "head")
            or _optional_string(parameters, "head_sha")
        )

        if not base:

            raise GitHubValidationError(
                "Missing required GitHub parameter: base"
            )

        if not head:

            raise GitHubValidationError(
                "Missing required GitHub parameter: head"
            )

        return self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/compare/{quote(base, safe='')}"
                f"...{quote(head, safe='')}",
            ),
        )

    def create_commit(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        """
        Low-level Git commit creation.

        Supports creating a commit from a supplied tree SHA and parent SHA.

        This is intentionally separate from create/update/delete file because
        those operations use GitHub's contents API.
        """

        owner, repository = self._resolve_repository(parameters)

        message = _require_string(
            parameters,
            "message",
        )

        tree_sha = _require_string(
            parameters,
            "tree_sha",
        )

        parent_sha = _optional_string(
            parameters,
            "parent_sha",
        )

        body: dict[str, Any] = {
            "message": message,
            "tree": tree_sha,
        }

        if parent_sha:

            body["parents"] = [parent_sha]

        return self._request(
            "POST",
            self._repo_path(
                owner,
                repository,
                "/git/commits",
            ),
            json=body,
        )

    # ------------------------------------------------------------------
    # PULL REQUESTS
    # ------------------------------------------------------------------

    def read_pull_request(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "pull_request_number",
        )

        return self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/pulls/{number}",
            ),
        )

    def list_pull_requests(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        params = self._pagination_parameters(parameters)

        state = _optional_string(
            parameters,
            "state",
        )

        head = _optional_string(
            parameters,
            "head",
        )

        base = _optional_string(
            parameters,
            "base",
        )

        if state:
            params["state"] = state

        if head:
            params["head"] = head

        if base:
            params["base"] = base

        data = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                "/pulls",
            ),
            params=params,
        )

        return {
            "repository": f"{owner}/{repository}",
            "pull_requests": data,
        }

    def inspect_pull_request_files(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "pull_request_number",
        )

        params = self._pagination_parameters(parameters)

        data = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/pulls/{number}/files",
            ),
            params=params,
        )

        return {
            "repository": f"{owner}/{repository}",
            "pull_request_number": number,
            "files": data,
        }

    def inspect_pull_request_diff(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "pull_request_number",
        )

        return self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/pulls/{number}",
            ),
            headers={
                "Accept": "application/vnd.github.v3.diff",
            },
        )

    def inspect_pull_request_reviews(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "pull_request_number",
        )

        params = self._pagination_parameters(parameters)

        data = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/pulls/{number}/reviews",
            ),
            params=params,
        )

        return {
            "repository": f"{owner}/{repository}",
            "pull_request_number": number,
            "reviews": data,
        }

    def inspect_review_threads(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        """
        GitHub's REST API does not expose the complete modern review-thread
        model in the same way as GraphQL.

        We therefore collect review comments and normalize them as review
        thread-like records.

        The optional file_path='unresolved' used by Falcon's parameter
        extractor is treated as a filter request rather than a real file path.
        """

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "pull_request_number",
        )

        params = self._pagination_parameters(parameters)

        comments = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/pulls/{number}/comments",
            ),
            params=params,
        )

        filter_value = _optional_string(
            parameters,
            "file_path",
        )

        normalized = []

        for comment in comments:

            body = comment.get("body")

            path = comment.get("path")

            normalized.append(
                {
                    "id": comment.get("id"),
                    "node_id": comment.get("node_id"),
                    "path": path,
                    "line": comment.get("line"),
                    "original_line": comment.get(
                        "original_line"
                    ),
                    "side": comment.get("side"),
                    "body": body,
                    "user": (
                        comment.get("user", {})
                        .get("login")
                    ),
                    "created_at": comment.get(
                        "created_at"
                    ),
                    "updated_at": comment.get(
                        "updated_at"
                    ),
                    "html_url": comment.get(
                        "html_url"
                    ),
                    "in_reply_to_id": comment.get(
                        "in_reply_to_id"
                    ),
                    "resolved": False,
                    "raw": comment,
                }
            )

        # Falcon currently uses "unresolved" as a request-level marker.
        # REST comments do not reliably expose the modern resolved-thread
        # state, so we do not falsely claim resolution.
        if filter_value and filter_value != "unresolved":

            normalized = [
                item
                for item in normalized
                if item["path"] == filter_value
            ]

        return {
            "repository": f"{owner}/{repository}",
            "pull_request_number": number,
            "threads": normalized,
            "resolution_state_available": False,
            "note": (
                "GitHub REST review comments were returned. "
                "Complete thread-resolution state may require GraphQL."
            ),
        }

    def resolve_review_thread(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        """
        Resolve a GitHub review thread.

        The REST API does not provide a universal REST mutation for modern
        review-thread resolution. Falcon therefore exposes a clear response
        rather than pretending that the operation succeeded.

        GraphQL support can be added later without changing the Falcon
        executor interface.
        """

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "pull_request_number",
        )

        thread_id = (
            parameters.get("thread_id")
            or parameters.get("review_thread_id")
        )

        if not thread_id:

            raise GitHubValidationError(
                "Missing required GitHub parameter: thread_id "
                "for resolve_review_thread."
            )

        return {
            "repository": f"{owner}/{repository}",
            "pull_request_number": number,
            "thread_id": thread_id,
            "resolved": False,
            "executed": False,
            "requires_graphql": True,
            "message": (
                "Review-thread resolution requires GitHub GraphQL "
                "resolveReviewThread mutation."
            ),
        }

    def create_pull_request(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        title = _require_string(
            parameters,
            "title",
        )

        head = _require_string(
            parameters,
            "head",
        )

        base = (
            _optional_string(
                parameters,
                "base",
            )
            or "main"
        )

        body = (
            _optional_string(
                parameters,
                "body",
            )
            or ""
        )

        payload: dict[str, Any] = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
        }

        draft = parameters.get("draft")

        if draft is not None:

            payload["draft"] = bool(draft)

        maintainer_can_modify = parameters.get(
            "maintainer_can_modify"
        )

        if maintainer_can_modify is not None:

            payload["maintainer_can_modify"] = bool(
                maintainer_can_modify
            )

        return self._request(
            "POST",
            self._repo_path(
                owner,
                repository,
                "/pulls",
            ),
            json=payload,
        )

    # ------------------------------------------------------------------
    # ISSUES
    # ------------------------------------------------------------------

    def read_issue(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "issue_number",
        )

        return self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/issues/{number}",
            ),
        )

    def list_issues(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        params = self._pagination_parameters(parameters)

        state = _optional_string(
            parameters,
            "state",
        )

        labels = _optional_string(
            parameters,
            "labels",
        )

        if state:
            params["state"] = state

        if labels:
            params["labels"] = labels

        data = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                "/issues",
            ),
            params=params,
        )

        return {
            "repository": f"{owner}/{repository}",
            "issues": data,
        }

    def update_issue(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "issue_number",
        )

        payload: dict[str, Any] = {}

        allowed = [
            "title",
            "body",
            "state",
            "state_reason",
            "milestone",
            "assignees",
            "labels",
        ]

        for field_name in allowed:

            if field_name in parameters:

                payload[field_name] = parameters[
                    field_name
                ]

        if not payload:

            raise GitHubValidationError(
                "No issue fields were supplied for update."
            )

        return self._request(
            "PATCH",
            self._repo_path(
                owner,
                repository,
                f"/issues/{number}",
            ),
            json=payload,
        )

    def create_issue(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        title = _require_string(
            parameters,
            "title",
        )

        payload: dict[str, Any] = {
            "title": title,
        }

        for field_name in [
            "body",
            "milestone",
            "assignees",
            "labels",
        ]:

            if field_name in parameters:

                payload[field_name] = parameters[
                    field_name
                ]

        return self._request(
            "POST",
            self._repo_path(
                owner,
                repository,
                "/issues",
            ),
            json=payload,
        )

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def inspect_job(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        job_number = _require_positive_int(
            parameters,
            "job_number",
        )

        return self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/actions/jobs/{job_number}",
            ),
        )

    def list_jobs(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        params = self._pagination_parameters(parameters)

        params["filter"] = (
            _optional_string(
                parameters,
                "filter",
            )
            or "latest"
        )

        data = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                "/actions/jobs",
            ),
            params=params,
        )

        return {
            "repository": f"{owner}/{repository}",
            "jobs": data,
        }

    def list_workflows(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        params = self._pagination_parameters(parameters)

        data = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                "/actions/workflows",
            ),
            params=params,
        )

        return {
            "repository": f"{owner}/{repository}",
            "workflows": data,
        }

    def inspect_workflow(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        workflow = _require_string(
            parameters,
            "workflow",
        )

        return self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/actions/workflows/{_encode_path(workflow)}",
            ),
        )

    def list_workflow_runs(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        workflow = _optional_string(
            parameters,
            "workflow",
        )

        params = self._pagination_parameters(parameters)

        if workflow:

            endpoint = self._repo_path(
                owner,
                repository,
                f"/actions/workflows/{_encode_path(workflow)}/runs",
            )

        else:

            endpoint = self._repo_path(
                owner,
                repository,
                "/actions/runs",
            )

        return self._request(
            "GET",
            endpoint,
            params=params,
        )

    def rerun_failed_job(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        job_number = _require_positive_int(
            parameters,
            "job_number",
        )

        return self._request(
            "POST",
            self._repo_path(
                owner,
                repository,
                f"/actions/jobs/{job_number}/rerun-failed-jobs",
            ),
        )

    def inspect_actions(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        params = self._pagination_parameters(parameters)

        runs = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                "/actions/runs",
            ),
            params=params,
        )

        return {
            "repository": f"{owner}/{repository}",
            "actions": runs,
        }

    def inspect_logs(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        job_number = parameters.get("job_number")

        run_number = parameters.get(
            "run_number"
        )

        if job_number:

            job_number = int(job_number)

            return self._request(
                "GET",
                self._repo_path(
                    owner,
                    repository,
                    f"/actions/jobs/{job_number}/logs",
                ),
                raw=True,
            )

        if run_number:

            run_number = int(run_number)

            return self._request(
                "GET",
                self._repo_path(
                    owner,
                    repository,
                    f"/actions/runs/{run_number}/logs",
                ),
                raw=True,
            )

        raise GitHubValidationError(
            "inspect_logs requires job_number or run_number."
        )

    # ------------------------------------------------------------------
    # CODE SEARCH
    # ------------------------------------------------------------------

    def search_code(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        query = _require_string(
            parameters,
            "query",
        )

        repository = (
            parameters.get("repository")
            or self.repository
        )

        if repository:

            owner, repo = _parse_repository(
                str(repository)
            )

            query = (
                f"{query} "
                f"repo:{owner}/{repo}"
            )

        params = {
            "q": query,
        }

        params.update(
            self._pagination_parameters(
                parameters
            )
        )

        data = self._request(
            "GET",
            "/search/code",
            params=params,
        )

        return data

    # ------------------------------------------------------------------
    # SEARCH ISSUES / PRS
    # ------------------------------------------------------------------

    def search_issues(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        query = _require_string(
            parameters,
            "query",
        )

        repository = (
            parameters.get("repository")
            or self.repository
        )

        if repository:

            owner, repo = _parse_repository(
                str(repository)
            )

            query = (
                f"{query} "
                f"repo:{owner}/{repo}"
            )

        params = {
            "q": query,
        }

        params.update(
            self._pagination_parameters(
                parameters
            )
        )

        return self._request(
            "GET",
            "/search/issues",
            params=params,
        )

    # ------------------------------------------------------------------
    # PR COMMENTS
    # ------------------------------------------------------------------

    def list_pull_request_comments(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "pull_request_number",
        )

        params = self._pagination_parameters(parameters)

        data = self._request(
            "GET",
            self._repo_path(
                owner,
                repository,
                f"/pulls/{number}/comments",
            ),
            params=params,
        )

        return {
            "repository": f"{owner}/{repository}",
            "pull_request_number": number,
            "comments": data,
        }

    def create_pull_request_comment(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "pull_request_number",
        )

        body = _require_string(
            parameters,
            "body",
        )

        payload: dict[str, Any] = {
            "body": body,
        }

        commit_id = _optional_string(
            parameters,
            "commit_id",
        )

        path = _optional_string(
            parameters,
            "path",
        )

        line = parameters.get("line")

        side = _optional_string(
            parameters,
            "side",
        )

        if commit_id:

            payload["commit_id"] = commit_id

        if path:

            payload["path"] = path

        if line is not None:

            payload["line"] = int(line)

        if side:

            payload["side"] = side

        in_reply_to = parameters.get(
            "in_reply_to"
        )

        if in_reply_to is not None:

            payload["in_reply_to"] = int(
                in_reply_to
            )

        return self._request(
            "POST",
            self._repo_path(
                owner,
                repository,
                f"/pulls/{number}/comments",
            ),
            json=payload,
        )

    # ------------------------------------------------------------------
    # PR REVIEW
    # ------------------------------------------------------------------

    def submit_pull_request_review(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        owner, repository = self._resolve_repository(parameters)

        number = _require_positive_int(
            parameters,
            "pull_request_number",
        )

        event = (
            _optional_string(
                parameters,
                "event",
            )
            or "COMMENT"
        )

        payload: dict[str, Any] = {
            "event": event,
        }

        body = _optional_string(
            parameters,
            "body",
        )

        if body:

            payload["body"] = body

        comments = parameters.get(
            "comments"
        )

        if comments is not None:

            payload["comments"] = comments

        return self._request(
            "POST",
            self._repo_path(
                owner,
                repository,
                f"/pulls/{number}/reviews",
            ),
            json=payload,
        )

    # ------------------------------------------------------------------
    # GITHUB REQUEST
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        raw: bool = False,
    ) -> Any:

        self._require_token()

        url = (
            endpoint
            if endpoint.startswith("http")
            else f"{self.api_url}{endpoint}"
        )

        request_headers = dict(
            self.session.headers
        )

        if headers:

            request_headers.update(headers)

        try:

            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=request_headers,
                timeout=self.timeout,
            )

        except requests.RequestException as exc:

            raise GitHubAPIError(
                f"GitHub network request failed: {exc}"
            ) from exc

        if response.status_code == 401:

            raise GitHubAuthenticationError(
                "GitHub authentication failed. "
                "Check the GitHub token."
            )

        if response.status_code == 403:

            remaining = response.headers.get(
                "X-RateLimit-Remaining"
            )

            if remaining == "0":

                raise GitHubRateLimitError(
                    "GitHub API rate limit reached."
                )

            raise GitHubPermissionError(
                self._error_message(
                    response,
                    fallback=(
                        "GitHub denied this operation."
                    ),
                )
            )

        if response.status_code == 404:

            raise GitHubNotFoundError(
                self._error_message(
                    response,
                    fallback=(
                        "GitHub resource was not found."
                    ),
                )
            )

        if response.status_code == 422:

            raise GitHubValidationError(
                self._error_message(
                    response,
                    fallback=(
                        "GitHub rejected the request."
                    ),
                )
            )

        if response.status_code >= 400:

            raise GitHubAPIError(
                self._error_message(
                    response,
                    fallback=(
                        f"GitHub API returned HTTP "
                        f"{response.status_code}."
                    ),
                )
            )

        if raw:

            return {
                "status_code": response.status_code,
                "content_type": response.headers.get(
                    "Content-Type"
                ),
                "content": response.text,
                "url": response.url,
            }

        if response.status_code == 204:

            return {
                "status_code": 204,
                "success": True,
            }

        try:

            return response.json()

        except ValueError:

            return {
                "status_code": response.status_code,
                "content": response.text,
                "url": response.url,
            }

    @staticmethod
    def _error_message(
        response: requests.Response,
        *,
        fallback: str,
    ) -> str:

        try:

            data = response.json()

            message = data.get(
                "message"
            )

            if message:

                return str(message)

            errors = data.get(
                "errors"
            )

            if errors:

                return str(errors)

        except ValueError:

            pass

        return fallback

    # ------------------------------------------------------------------
    # UNIVERSAL EXECUTION DISPATCHER
    # ------------------------------------------------------------------

    def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> Any:

        operation = str(
            operation
        ).strip()

        parameters = dict(
            parameters or {}
        )

        handlers = {
            # Authentication
            "get_authenticated_user":
                self._execute_get_authenticated_user,

            # Repository
            "inspect_repository":
                self.get_repository,

            "list_branches":
                self.get_repository_branches,

            # Files
            "read_file":
                self.read_file,

            "create_file":
                self.create_file,

            "update_file":
                self.update_file,

            "delete_file":
                self.delete_file,

            # Branches
            "inspect_branch":
                self.inspect_branch,

            "create_branch":
                self.create_branch,

            # Commits
            "inspect_commit":
                self.inspect_commit,

            "list_commits":
                self.list_commits,

            "compare_commits":
                self.compare_commits,

            "create_commit":
                self.create_commit,

            # Pull requests
            "read_pull_request":
                self.read_pull_request,

            "list_pull_requests":
                self.list_pull_requests,

            "inspect_pull_request_files":
                self.inspect_pull_request_files,

            "inspect_pull_request_diff":
                self.inspect_pull_request_diff,

            "inspect_pull_request_reviews":
                self.inspect_pull_request_reviews,

            "inspect_review_threads":
                self.inspect_review_threads,

            "resolve_review_thread":
                self.resolve_review_thread,

            "create_pull_request":
                self.create_pull_request,

            "list_pull_request_comments":
                self.list_pull_request_comments,

            "create_pull_request_comment":
                self.create_pull_request_comment,

            "submit_pull_request_review":
                self.submit_pull_request_review,

            # Issues
            "read_issue":
                self.read_issue,

            "list_issues":
                self.list_issues,

            "update_issue":
                self.update_issue,

            "create_issue":
                self.create_issue,

            # Actions
            "inspect_job":
                self.inspect_job,

            "list_jobs":
                self.list_jobs,

            "list_workflows":
                self.list_workflows,

            "inspect_workflow":
                self.inspect_workflow,

            "list_workflow_runs":
                self.list_workflow_runs,

            "rerun_failed_job":
                self.rerun_failed_job,

            "inspect_actions":
                self.inspect_actions,

            "inspect_logs":
                self.inspect_logs,

            # Search
            "search_code":
                self.search_code,

            "search_issues":
                self.search_issues,
        }

        handler = handlers.get(
            operation
        )

        if handler is None:

            raise GitHubValidationError(
                f"Unsupported GitHub operation: {operation}"
            )

        return handler(
            parameters
        )

    def _execute_get_authenticated_user(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        return self.get_authenticated_user()


# ============================================================================
# FACTORY
# ============================================================================


def create_github_client() -> GitHubClient:
    """
    Create a configured Falcon GitHub client.

    The token and repository are loaded from environment variables.
    """

    return GitHubClient()


# ============================================================================
# BACKWARD-COMPATIBILITY ALIAS
# ============================================================================


RealGitHubClient = GitHubClient


# ============================================================================
# LOCAL MANUAL TEST ENTRYPOINT
# ============================================================================


if __name__ == "__main__":

    print(
        "Falcon GitHub client module loaded."
    )

    token_configured = bool(
        os.getenv("FALCON_GITHUB_TOKEN")
        or os.getenv("GITHUB_TOKEN")
    )

    repository = (
        os.getenv("FALCON_GITHUB_REPOSITORY")
        or os.getenv("GITHUB_REPOSITORY")
    )

    print(
        f"GitHub token configured: "
        f"{token_configured}"
    )

    print(
        f"Default repository: "
        f"{repository or 'not configured'}"
    )

    print(
        "No GitHub API request was executed."
    )
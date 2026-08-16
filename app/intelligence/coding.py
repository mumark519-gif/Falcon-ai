from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# ============================================================
# DATA MODEL
# ============================================================


@dataclass
class CodingTask:
    """
    Represents a coding task managed by Falcon.
    """

    goal: str
    repository: str | None = None
    files: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    status: str = "planned"
    result: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# CODING CONTROLLER
# ============================================================


class CodingController:
    """
    Falcon coding workflow controller.

    Responsibilities:

    1. Inspect a repository.
    2. Identify relevant source files.
    3. Create structured coding tasks.
    4. Track task state.
    5. Read source files safely.
    6. Write source files safely.
    7. Run configured tests when requested.
    8. Return structured results.

    This controller deliberately does not execute arbitrary
    shell commands. Command execution should remain behind
    Falcon's existing tool/permission system.
    """

    DEFAULT_LIMIT = 500
    MAX_FILE_SIZE = 5 * 1024 * 1024

    SOURCE_EXTENSIONS = {
        ".py",
        ".pyi",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".kt",
        ".kts",
        ".go",
        ".rs",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cc",
        ".cs",
        ".php",
        ".rb",
        ".swift",
        ".sql",
        ".html",
        ".css",
        ".scss",
        ".sass",
        ".vue",
        ".svelte",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".md",
        ".txt",
    }

    IGNORED_DIRECTORIES = {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "coverage",
        ".idea",
        ".vscode",
    }

    # ========================================================
    # PATH HELPERS
    # ========================================================

    def _root(self, root: str) -> Path:
        """
        Resolve and validate a repository root.
        """

        if not str(root).strip():
            raise ValueError(
                "Repository root cannot be empty."
            )

        path = Path(root).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(
                f"Repository does not exist: {root}"
            )

        if not path.is_dir():
            raise NotADirectoryError(
                f"Repository path is not a directory: {root}"
            )

        return path

    def _relative_path(
        self,
        root: Path,
        path: Path,
    ) -> str:
        return str(
            path.relative_to(root)
        ).replace("\\", "/")

    def _is_ignored(
        self,
        root: Path,
        path: Path,
    ) -> bool:
        try:
            relative = path.relative_to(root)
        except ValueError:
            return True

        return any(
            part in self.IGNORED_DIRECTORIES
            for part in relative.parts
        )

    # ========================================================
    # REPOSITORY INSPECTION
    # ========================================================

    def inspect_tree(
        self,
        root: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[str]:
        """
        Return repository files relative to the repository root.
        """

        if limit <= 0:
            return []

        repository = self._root(root)

        files: list[str] = []

        for path in repository.rglob("*"):
            if not path.is_file():
                continue

            if self._is_ignored(
                repository,
                path,
            ):
                continue

            files.append(
                self._relative_path(
                    repository,
                    path,
                )
            )

            if len(files) >= limit:
                break

        return sorted(files)

    def inspect_source_tree(
        self,
        root: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[str]:
        """
        Return only files that look like source/configuration/
        documentation files relevant to coding work.
        """

        all_files = self.inspect_tree(
            root=root,
            limit=max(
                limit * 3,
                limit,
            ),
        )

        source_files = [
            path
            for path in all_files
            if Path(path).suffix.lower()
            in self.SOURCE_EXTENSIONS
        ]

        return source_files[:limit]

    def repository_summary(
        self,
        root: str,
    ) -> dict[str, Any]:
        """
        Produce a lightweight repository summary.
        """

        repository = self._root(root)

        files = self.inspect_tree(
            root,
            self.DEFAULT_LIMIT,
        )

        source_files = [
            path
            for path in files
            if Path(path).suffix.lower()
            in self.SOURCE_EXTENSIONS
        ]

        extensions: dict[str, int] = {}

        for path in files:
            extension = Path(path).suffix.lower()

            if not extension:
                extension = "<none>"

            extensions[extension] = (
                extensions.get(
                    extension,
                    0,
                )
                + 1
            )

        return {
            "repository": str(repository),
            "total_files": len(files),
            "source_files": len(source_files),
            "files": files,
            "extensions": extensions,
        }

    # ========================================================
    # TASK CREATION
    # ========================================================

    def create_task(
        self,
        goal: str,
        repository: str | None = None,
    ) -> CodingTask:
        """
        Create a validated coding task.
        """

        normalized_goal = str(
            goal or ""
        ).strip()

        if not normalized_goal:
            raise ValueError(
                "Coding task goal cannot be empty."
            )

        normalized_repository = None

        if repository is not None:
            normalized_repository = str(
                repository
            ).strip() or None

        return CodingTask(
            goal=normalized_goal,
            repository=normalized_repository,
        )

    # ========================================================
    # TASK PREPARATION
    # ========================================================

    def prepare_task(
        self,
        task: CodingTask,
        limit: int = DEFAULT_LIMIT,
    ) -> CodingTask:
        """
        Inspect the task repository and attach the available
        source files to the task.
        """

        if not isinstance(
            task,
            CodingTask,
        ):
            raise TypeError(
                "task must be a CodingTask."
            )

        if not task.repository:
            task.status = "ready"
            return task

        task.files = self.inspect_source_tree(
            task.repository,
            limit=limit,
        )

        task.status = "ready"

        return task

    # ========================================================
    # FILE READING
    # ========================================================

    def read_file(
        self,
        root: str,
        file_path: str,
    ) -> str:
        """
        Read a repository file while preventing path traversal
        outside the repository root.
        """

        repository = self._root(root)

        requested = Path(
            file_path
        )

        if requested.is_absolute():
            target = requested.resolve()
        else:
            target = (
                repository / requested
            ).resolve()

        try:
            target.relative_to(
                repository
            )
        except ValueError as exc:
            raise PermissionError(
                "File path is outside the repository."
            ) from exc

        if not target.exists():
            raise FileNotFoundError(
                f"File does not exist: {file_path}"
            )

        if not target.is_file():
            raise IsADirectoryError(
                f"Path is not a file: {file_path}"
            )

        size = target.stat().st_size

        if size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File exceeds the maximum supported size "
                f"of {self.MAX_FILE_SIZE} bytes."
            )

        return target.read_text(
            encoding="utf-8"
        )

    # ========================================================
    # FILE WRITING
    # ========================================================

    def write_file(
        self,
        root: str,
        file_path: str,
        content: str,
        create_parents: bool = True,
    ) -> dict[str, Any]:
        """
        Write a file inside the repository.

        This method intentionally operates only inside the
        supplied repository root.
        """

        repository = self._root(root)

        if not isinstance(
            content,
            str,
        ):
            raise TypeError(
                "File content must be a string."
            )

        requested = Path(
            file_path
        )

        if requested.is_absolute():
            target = requested.resolve()
        else:
            target = (
                repository / requested
            ).resolve()

        try:
            target.relative_to(
                repository
            )
        except ValueError as exc:
            raise PermissionError(
                "File path is outside the repository."
            ) from exc

        if create_parents:
            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        target.write_text(
            content,
            encoding="utf-8",
        )

        return {
            "status": "success",
            "file": self._relative_path(
                repository,
                target,
            ),
            "bytes": target.stat().st_size,
        }

    # ========================================================
    # FILE DISCOVERY
    # ========================================================

    def find_files(
        self,
        root: str,
        query: str,
        limit: int = 50,
    ) -> list[str]:
        """
        Find repository files whose names contain the query.
        """

        normalized_query = str(
            query or ""
        ).strip().lower()

        if not normalized_query:
            return []

        files = self.inspect_tree(
            root=root,
            limit=self.DEFAULT_LIMIT * 2,
        )

        matches = [
            path
            for path in files
            if normalized_query
            in Path(path).name.lower()
        ]

        return matches[:limit]

    # ========================================================
    # TEST REGISTRATION
    # ========================================================

    def add_test(
        self,
        task: CodingTask,
        test: str,
    ) -> CodingTask:
        """
        Attach a test command/specification to a coding task.

        Actual execution remains delegated to Falcon's
        controlled tool execution layer.
        """

        if not isinstance(
            task,
            CodingTask,
        ):
            raise TypeError(
                "task must be a CodingTask."
            )

        normalized_test = str(
            test or ""
        ).strip()

        if not normalized_test:
            raise ValueError(
                "Test cannot be empty."
            )

        if normalized_test not in task.tests:
            task.tests.append(
                normalized_test
            )

        return task

    # ========================================================
    # TASK STATE
    # ========================================================

    def mark_running(
        self,
        task: CodingTask,
    ) -> CodingTask:
        task.status = "running"
        task.error = None
        return task

    def mark_complete(
        self,
        task: CodingTask,
        result: Any = None,
    ) -> CodingTask:
        task.status = "complete"
        task.result = result
        task.error = None
        return task

    def mark_failed(
        self,
        task: CodingTask,
        error: str,
    ) -> CodingTask:
        task.status = "failed"
        task.error = str(error)
        return task

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def task_to_dict(
        self,
        task: CodingTask,
    ) -> dict[str, Any]:
        """
        Convert a coding task to a JSON-friendly dictionary.
        """

        if not isinstance(
            task,
            CodingTask,
        ):
            raise TypeError(
                "task must be a CodingTask."
            )

        return task.to_dict()


# ============================================================
# SHARED CONTROLLER
# ============================================================


coding_controller = CodingController()

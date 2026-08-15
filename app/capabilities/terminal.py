from __future__ import annotations
import shlex
import subprocess
from pathlib import Path

from app.core.settings import settings
from app.security.sandbox import Sandbox

# Commands/patterns that are never allowed, regardless of approval.
# This is not a substitute for real OS-level sandboxing (a container or
# VM boundary) -- it's a last-resort guard against the most catastrophic
# single-command mistakes an agent could make or be prompted into making.
_HARD_DENYLIST = (
    "rm -rf /", "rm -rf /*", "rm -rf ~", "rm -rf .",
    ":(){ :|:& };:",  # fork bomb
    "mkfs", "dd if=", "> /dev/sda", "shutdown", "reboot", "init 0",
    "chmod -r 777 /", "chown -r", "sudo ", "su -",
    "curl | sh", "curl | bash", "wget | sh", "wget | bash",
)

# Commands that modify state and therefore require explicit approval
# when FALCON_REQUIRE_WRITE_APPROVAL is set (the default).
_WRITE_PREFIXES = (
    "rm ", "mv ", "cp ", "chmod ", "chown ", "git push", "git commit",
    "pip install", "npm install", "npm uninstall", "apt", "apt-get",
    ">", ">>",
)


class TerminalPermissionError(PermissionError):
    """Raised when a command is blocked or needs approval that wasn't given."""


class TerminalCapability:
    """Runs shell commands confined to a sandbox root, with a hard denylist
    for destructive patterns and an approval gate for write-like commands.

    This mirrors the intent of app.security.policy.SecurityPolicy and
    app.intelligence.computer_use.ComputerUsePolicy, which define approval
    rules elsewhere in Falcon but previously weren't connected to this
    capability at all.
    """

    def __init__(self, root: str = "./data/sandbox"):
        self.sandbox = Sandbox(root)

    def _check_denylist(self, command: str) -> None:
        lowered = command.lower()
        for pattern in _HARD_DENYLIST:
            if pattern in lowered:
                raise TerminalPermissionError(
                    f"Command blocked by Falcon's terminal safety policy: "
                    f"matches denied pattern '{pattern}'."
                )

    def _needs_approval(self, command: str) -> bool:
        if not settings.require_write_approval:
            return False
        lowered = command.strip().lower()
        return any(lowered.startswith(p) or f" {p}" in lowered for p in _WRITE_PREFIXES)

    def run(
        self,
        command: str,
        timeout: int = 60,
        cwd: str = ".",
        approved: bool = False,
    ) -> dict:
        """Execute `command` inside the sandbox root.

        `cwd` is resolved relative to the sandbox root and cannot escape it.
        Write-like commands (rm, mv, git push, pip install, redirects, etc.)
        require `approved=True` when FALCON_REQUIRE_WRITE_APPROVAL is on --
        mirroring the approval gate already defined for other capabilities.
        """
        if not command or not command.strip():
            return {"success": False, "error": "Command is empty.", "returncode": None}

        self._check_denylist(command)

        if self._needs_approval(command) and not approved:
            return {
                "success": False,
                "returncode": None,
                "error": (
                    "This command modifies files or state and requires "
                    "explicit approval (approved=True) before Falcon will "
                    "run it."
                ),
                "requires_approval": True,
            }

        try:
            safe_cwd = self.sandbox.safe_path(cwd)
        except PermissionError as exc:
            return {"success": False, "error": str(exc), "returncode": None}

        safe_cwd.mkdir(parents=True, exist_ok=True)

        try:
            p = subprocess.run(
                command,
                shell=True,
                cwd=safe_cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "returncode": p.returncode,
                "stdout": p.stdout,
                "stderr": p.stderr,
                "success": p.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": None,
                "error": f"Command timed out after {timeout}s.",
            }

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


# ============================================================
# ACTION MODEL
# ============================================================


@dataclass
class Action:
    """
    Represents a computer-use action requested by Falcon.

    This model describes an action. It does not execute it.
    Actual computer interaction must remain behind a
    controlled execution/tool layer.
    """

    kind: str
    target: str | None = None
    value: str | None = None
    requires_confirmation: bool = True

    def normalized_kind(self) -> str:
        return str(
            self.kind or ""
        ).strip().lower()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# COMPUTER-USE POLICY
# ============================================================


class ComputerUsePolicy:
    """
    Central authorization policy for Falcon computer-use actions.

    The policy distinguishes between:

    SAFE
        Actions that are generally non-destructive.

    SENSITIVE
        Actions that can create external side effects and
        therefore require explicit approval.

    BLOCKED
        Actions that Falcon's computer-use layer must not
        perform through this policy.

    This class only authorizes actions. It never performs them.
    """

    SAFE = {
        "screenshot",
        "move_mouse",
        "click",
        "type_text",
        "scroll",
        "navigate",
        "open",
        "focus",
        "select",
        "keypress",
        "copy",
        "read",
        "inspect",
    }

    SENSITIVE = {
        "download",
        "upload",
        "purchase",
        "send_message",
        "send_email",
        "delete",
        "submit_form",
        "publish",
        "post",
        "transfer",
        "payment",
        "checkout",
        "install",
        "uninstall",
        "change_settings",
        "create_account",
        "close_account",
    }

    BLOCKED = {
        "credential_exfiltration",
        "password_export",
        "secret_export",
        "security_bypass",
        "captcha_bypass",
        "malware_execution",
    }

    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def normalize_action(
        action: Action,
    ) -> Action:
        """
        Normalize an Action object without changing its intent.
        """

        if not isinstance(
            action,
            Action,
        ):
            raise TypeError(
                "action must be an Action instance."
            )

        return Action(
            kind=action.normalized_kind(),
            target=(
                str(action.target).strip()
                if action.target is not None
                else None
            ),
            value=(
                str(action.value)
                if action.value is not None
                else None
            ),
            requires_confirmation=bool(
                action.requires_confirmation
            ),
        )

    # ========================================================
    # CLASSIFICATION
    # ========================================================

    def classify(
        self,
        action: Action,
    ) -> str:
        """
        Classify an action as:

        safe
        sensitive
        blocked
        unknown
        """

        normalized = self.normalize_action(
            action
        )

        kind = normalized.normalized_kind()

        if kind in self.BLOCKED:
            return "blocked"

        if kind in self.SENSITIVE:
            return "sensitive"

        if kind in self.SAFE:
            return "safe"

        return "unknown"

    # ========================================================
    # CONFIRMATION
    # ========================================================

    def requires_confirmation(
        self,
        action: Action,
    ) -> bool:
        """
        Determine whether an action requires explicit user
        confirmation.
        """

        normalized = self.normalize_action(
            action
        )

        classification = self.classify(
            normalized
        )

        if classification in {
            "blocked",
            "unknown",
        }:
            return True

        if classification == "sensitive":
            return True

        return bool(
            normalized.requires_confirmation
        )

    # ========================================================
    # AUTHORIZATION
    # ========================================================

    def authorize(
        self,
        action: Action,
        approved: bool = False,
    ) -> bool:
        """
        Determine whether Falcon may proceed with an action.

        Safe actions may proceed when their own action policy
        allows them.

        Sensitive actions require explicit approval.

        Blocked and unknown actions are denied.
        """

        normalized = self.normalize_action(
            action
        )

        classification = self.classify(
            normalized
        )

        if classification == "blocked":
            return False

        if classification == "unknown":
            return False

        if classification == "sensitive":
            return bool(approved)

        if normalized.requires_confirmation:
            return bool(approved)

        return True

    # ========================================================
    # DECISION
    # ========================================================

    def evaluate(
        self,
        action: Action,
        approved: bool = False,
    ) -> dict[str, Any]:
        """
        Return a structured authorization decision.

        This is preferable to exposing only a boolean because
        Falcon's orchestration layer needs to know why an action
        was accepted or rejected.
        """

        normalized = self.normalize_action(
            action
        )

        classification = self.classify(
            normalized
        )

        authorized = self.authorize(
            normalized,
            approved=approved,
        )

        if classification == "blocked":
            reason = (
                "This computer-use action is blocked by "
                "Falcon's security policy."
            )

        elif classification == "unknown":
            reason = (
                "Unknown computer-use actions require an "
                "explicitly supported capability."
            )

        elif classification == "sensitive" and not approved:
            reason = (
                "This action requires explicit user "
                "confirmation before execution."
            )

        elif authorized:
            reason = (
                "Action is authorized by the current "
                "computer-use policy."
            )

        else:
            reason = (
                "Action was not authorized by the current "
                "computer-use policy."
            )

        return {
            "authorized": authorized,
            "classification": classification,
            "requires_confirmation": (
                self.requires_confirmation(
                    normalized
                )
            ),
            "reason": reason,
            "action": normalized.to_dict(),
        }

    # ========================================================
    # BATCH EVALUATION
    # ========================================================

    def evaluate_many(
        self,
        actions: list[Action],
        approved: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Evaluate multiple actions independently.

        One denied action does not automatically alter the
        classification of the others.
        """

        if not isinstance(
            actions,
            list,
        ):
            raise TypeError(
                "actions must be a list."
            )

        return [
            self.evaluate(
                action,
                approved=approved,
            )
            for action in actions
        ]

    # ========================================================
    # CAPABILITY CHECK
    # ========================================================

    def is_supported(
        self,
        kind: str,
    ) -> bool:
        """
        Return whether the action type is explicitly known.
        """

        normalized = str(
            kind or ""
        ).strip().lower()

        return normalized in (
            self.SAFE
            | self.SENSITIVE
            | self.BLOCKED
        )

    def is_safe(
        self,
        kind: str,
    ) -> bool:
        """
        Return whether the action type belongs to the safe set.
        """

        normalized = str(
            kind or ""
        ).strip().lower()

        return normalized in self.SAFE

    def is_sensitive(
        self,
        kind: str,
    ) -> bool:
        """
        Return whether the action type requires confirmation.
        """

        normalized = str(
            kind or ""
        ).strip().lower()

        return normalized in self.SENSITIVE

    def is_blocked(
        self,
        kind: str,
    ) -> bool:
        """
        Return whether the action type is blocked.
        """

        normalized = str(
            kind or ""
        ).strip().lower()

        return normalized in self.BLOCKED


# ============================================================
# SHARED POLICY INSTANCE
# ============================================================


computer_use_policy = ComputerUsePolicy()


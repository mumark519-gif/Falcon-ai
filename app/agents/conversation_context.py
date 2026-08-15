from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Any


MAX_MESSAGES = 100
MAX_CONTEXT_ITEMS = 100
MAX_REFERENCES = 100


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _copy(value: Any) -> Any:
    try:
        return deepcopy(value)
    except Exception:
        return value


class ConversationContext:
    """
    Stateful context for one Falcon conversation.

    Responsibilities:

    - store recent messages
    - store important facts
    - store active task information
    - store references to previous results
    - track current topic
    - track entities mentioned in conversation
    - expose compact context to reasoning/planning
    """

    def __init__(
        self,
        conversation_id: str,
        username: str = "",
    ) -> None:

        self.conversation_id = str(
            conversation_id or ""
        ).strip()

        self.username = str(
            username or ""
        ).strip()

        self.created_at = _now()
        self.updated_at = self.created_at

        self._messages: list[dict[str, Any]] = []
        self._facts: dict[str, Any] = {}
        self._context: dict[str, Any] = {}
        self._references: list[dict[str, Any]] = []
        self._entities: dict[str, Any] = {}

        self._current_topic = ""

        self._lock = RLock()

    # ========================================================
    # MESSAGE MANAGEMENT
    # ========================================================

    def add_message(
        self,
        role: str,
        content: Any,
        *,
        message_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        message = {
            "id": message_id,
            "role": str(role or "").strip().lower(),
            "content": _copy(content),
            "timestamp": _now(),
            "metadata": _copy(metadata or {}),
        }

        with self._lock:

            self._messages.append(message)

            self._messages = self._messages[
                -MAX_MESSAGES:
            ]

            self.updated_at = _now()

        return _copy(message)

    def messages(self) -> list[dict[str, Any]]:
        with self._lock:
            return _copy(self._messages)

    def recent_messages(
        self,
        limit: int = 20,
    ) -> list[dict[str, Any]]:

        try:
            limit = max(1, int(limit))
        except (TypeError, ValueError):
            limit = 20

        with self._lock:
            return _copy(
                self._messages[-limit:]
            )

    # ========================================================
    # FACTS
    # ========================================================

    def set_fact(
        self,
        key: str,
        value: Any,
        *,
        confidence: float = 1.0,
        source: str = "conversation",
    ) -> None:

        key = str(key or "").strip()

        if not key:
            return

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.5

        confidence = max(
            0.0,
            min(1.0, confidence),
        )

        with self._lock:

            self._facts[key] = {
                "value": _copy(value),
                "confidence": confidence,
                "source": source,
                "updated_at": _now(),
            }

            self.updated_at = _now()

    def get_fact(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        key = str(key or "").strip()

        with self._lock:

            item = self._facts.get(key)

            if item is None:
                return default

            return _copy(
                item.get(
                    "value",
                    default,
                )
            )

    def facts(self) -> dict[str, Any]:

        with self._lock:
            return _copy(self._facts)

    def remove_fact(
        self,
        key: str,
    ) -> bool:

        key = str(key or "").strip()

        with self._lock:

            if key not in self._facts:
                return False

            del self._facts[key]

            self.updated_at = _now()

            return True

    # ========================================================
    # GENERAL CONTEXT
    # ========================================================

    def set_context(
        self,
        key: str,
        value: Any,
    ) -> None:

        key = str(key or "").strip()

        if not key:
            return

        with self._lock:

            self._context[key] = _copy(value)

            if len(self._context) > MAX_CONTEXT_ITEMS:

                oldest_key = next(
                    iter(self._context)
                )

                del self._context[
                    oldest_key
                ]

            self.updated_at = _now()

    def get_context(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        with self._lock:
            return _copy(
                self._context.get(
                    key,
                    default,
                )
            )

    def context(self) -> dict[str, Any]:

        with self._lock:
            return _copy(
                self._context
            )

    # ========================================================
    # REFERENCES
    # ========================================================

    def add_reference(
        self,
        reference_type: str,
        value: Any,
        *,
        label: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        reference = {
            "type": str(
                reference_type or ""
            ).strip(),

            "label": str(
                label or ""
            ).strip(),

            "value": _copy(value),

            "metadata": _copy(
                metadata or {}
            ),

            "timestamp": _now(),
        }

        with self._lock:

            self._references.append(
                reference
            )

            self._references = self._references[
                -MAX_REFERENCES:
            ]

            self.updated_at = _now()

        return _copy(reference)

    def references(
        self,
    ) -> list[dict[str, Any]]:

        with self._lock:
            return _copy(
                self._references
            )

    # ========================================================
    # ENTITIES
    # ========================================================

    def set_entity(
        self,
        name: str,
        data: Any,
    ) -> None:

        name = str(name or "").strip()

        if not name:
            return

        with self._lock:

            self._entities[name] = _copy(data)

            self.updated_at = _now()

    def get_entity(
        self,
        name: str,
        default: Any = None,
    ) -> Any:

        name = str(name or "").strip()

        with self._lock:

            return _copy(
                self._entities.get(
                    name,
                    default,
                )
            )

    def entities(
        self,
    ) -> dict[str, Any]:

        with self._lock:
            return _copy(
                self._entities
            )

    # ========================================================
    # TOPIC
    # ========================================================

    def set_topic(
        self,
        topic: str,
    ) -> None:

        with self._lock:

            self._current_topic = str(
                topic or ""
            ).strip()

            self.updated_at = _now()

    def topic(self) -> str:

        with self._lock:
            return self._current_topic

    # ========================================================
    # TASK
    # ========================================================

    def set_active_task(
        self,
        task_id: str,
        task_data: Any = None,
    ) -> None:

        self.set_context(
            "active_task",
            {
                "task_id": str(
                    task_id or ""
                ),
                "data": _copy(task_data),
                "updated_at": _now(),
            },
        )

    def active_task(
        self,
    ) -> dict[str, Any] | None:

        value = self.get_context(
            "active_task"
        )

        if not isinstance(value, dict):
            return None

        return value

    # ========================================================
    # COMPACT CONTEXT
    # ========================================================

    def build_prompt_context(
        self,
        *,
        message_limit: int = 20,
    ) -> dict[str, Any]:

        with self._lock:

            return {
                "conversation_id": self.conversation_id,
                "username": self.username,
                "current_topic": self._current_topic,
                "recent_messages": _copy(
                    self._messages[
                        -message_limit:
                    ]
                ),
                "facts": _copy(
                    self._facts
                ),
                "context": _copy(
                    self._context
                ),
                "references": _copy(
                    self._references
                ),
                "entities": _copy(
                    self._entities
                ),
            }

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def snapshot(self) -> dict[str, Any]:

        return {
            "conversation_id": self.conversation_id,
            "username": self.username,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_topic": self.topic(),
            "messages": self.messages(),
            "facts": self.facts(),
            "context": self.context(),
            "references": self.references(),
            "entities": self.entities(),
        }

    # ========================================================
    # RESTORE
    # ========================================================

    @classmethod
    def from_snapshot(
        cls,
        snapshot: dict[str, Any],
    ) -> "ConversationContext":

        if not isinstance(
            snapshot,
            dict,
        ):
            raise TypeError(
                "Conversation snapshot must be a dictionary."
            )

        context = cls(
            conversation_id=str(
                snapshot.get(
                    "conversation_id",
                    "",
                )
            ),
            username=str(
                snapshot.get(
                    "username",
                    "",
                )
            ),
        )

        context.created_at = str(
            snapshot.get(
                "created_at",
                context.created_at,
            )
        )

        context.updated_at = str(
            snapshot.get(
                "updated_at",
                context.updated_at,
            )
        )

        context._messages = _copy(
            snapshot.get(
                "messages",
                [],
            )
        )

        context._facts = _copy(
            snapshot.get(
                "facts",
                {},
            )
        )

        context._context = _copy(
            snapshot.get(
                "context",
                {},
            )
        )

        context._references = _copy(
            snapshot.get(
                "references",
                [],
            )
        )

        context._entities = _copy(
            snapshot.get(
                "entities",
                {},
            )
        )

        context._current_topic = str(
            snapshot.get(
                "current_topic",
                "",
            )
        )

        return context


# ============================================================
# GLOBAL CONVERSATION STORE
# ============================================================

class ConversationContextStore:

    def __init__(self) -> None:

        self._conversations: dict[
            str,
            ConversationContext,
        ] = {}

        self._lock = RLock()

    def create(
        self,
        conversation_id: str,
        username: str = "",
    ) -> ConversationContext:

        conversation_id = str(
            conversation_id or ""
        ).strip()

        if not conversation_id:
            raise ValueError(
                "Conversation ID is required."
            )

        with self._lock:

            if conversation_id in self._conversations:
                return self._conversations[
                    conversation_id
                ]

            context = ConversationContext(
                conversation_id=conversation_id,
                username=username,
            )

            self._conversations[
                conversation_id
            ] = context

            return context

    def get(
        self,
        conversation_id: str,
    ) -> ConversationContext | None:

        with self._lock:

            return self._conversations.get(
                str(
                    conversation_id or ""
                ).strip()
            )

    def get_or_create(
        self,
        conversation_id: str,
        username: str = "",
    ) -> ConversationContext:

        existing = self.get(
            conversation_id
        )

        if existing is not None:
            return existing

        return self.create(
            conversation_id,
            username,
        )

    def delete(
        self,
        conversation_id: str,
    ) -> bool:

        conversation_id = str(
            conversation_id or ""
        ).strip()

        with self._lock:

            if conversation_id not in self._conversations:
                return False

            del self._conversations[
                conversation_id
            ]

            return True

    def clear(self) -> None:

        with self._lock:
            self._conversations.clear()


conversation_store = ConversationContextStore()
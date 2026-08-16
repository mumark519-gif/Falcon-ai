from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


# ============================================================
# CONTEXT MESSAGE
# ============================================================


@dataclass
class ContextMessage:
    """
    One normalized message inside Falcon's context window.
    """

    role: str
    content: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            **self.metadata,
        }


# ============================================================
# CONTEXT WINDOW
# ============================================================


@dataclass
class ContextWindow:
    """
    Structured context window for Falcon's intelligence layer.

    Stores:

    - system instructions
    - conversation messages
    - memories
    - document context
    - additional structured context

    The window automatically keeps the most recent messages
    according to max_items.
    """

    system: str = ""
    messages: list[dict[str, Any]] = field(
        default_factory=list
    )
    memories: list[str] = field(
        default_factory=list
    )
    documents: list[str] = field(
        default_factory=list
    )
    max_items: int = 50
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __post_init__(self) -> None:
        if self.max_items < 1:
            self.max_items = 1

        self.system = str(
            self.system or ""
        ).strip()

        self._trim_messages()

    # ========================================================
    # MESSAGE MANAGEMENT
    # ========================================================

    def add(
        self,
        role: str,
        content: str,
        **meta: Any,
    ) -> None:
        """
        Add one message to the context window.
        """

        normalized_role = str(
            role or "user"
        ).strip()

        normalized_content = str(
            content or ""
        )

        message = {
            "role": normalized_role,
            "content": normalized_content,
            **meta,
        }

        self.messages.append(
            message
        )

        self._trim_messages()

    def add_message(
        self,
        message: ContextMessage,
    ) -> None:
        """
        Add a ContextMessage object.
        """

        if not isinstance(
            message,
            ContextMessage,
        ):
            raise TypeError(
                "message must be a ContextMessage."
            )

        self.messages.append(
            message.to_dict()
        )

        self._trim_messages()

    def add_user_message(
        self,
        content: str,
        **meta: Any,
    ) -> None:
        self.add(
            "user",
            content,
            **meta,
        )

    def add_assistant_message(
        self,
        content: str,
        **meta: Any,
    ) -> None:
        self.add(
            "assistant",
            content,
            **meta,
        )

    def add_system_message(
        self,
        content: str,
        **meta: Any,
    ) -> None:
        self.add(
            "system",
            content,
            **meta,
        )

    def add_tool_message(
        self,
        content: str,
        **meta: Any,
    ) -> None:
        self.add(
            "tool",
            content,
            **meta,
        )

    def _trim_messages(self) -> None:
        """
        Keep only the newest max_items messages.
        """

        if self.max_items < 1:
            self.messages = []

            return

        if len(self.messages) > self.max_items:
            self.messages = self.messages[
                -self.max_items:
            ]

    # ========================================================
    # MEMORY MANAGEMENT
    # ========================================================

    def add_memory(
        self,
        memory: str,
    ) -> None:
        """
        Add a memory to the context.
        """

        value = str(
            memory or ""
        ).strip()

        if not value:
            return

        self.memories.append(
            value
        )

    def add_memories(
        self,
        memories: list[str],
    ) -> None:
        """
        Add multiple memories.
        """

        if not isinstance(
            memories,
            list,
        ):
            return

        for memory in memories:
            self.add_memory(
                memory
            )

    # ========================================================
    # DOCUMENT MANAGEMENT
    # ========================================================

    def add_document(
        self,
        document: str,
    ) -> None:
        """
        Add document context.
        """

        value = str(
            document or ""
        ).strip()

        if not value:
            return

        self.documents.append(
            value
        )

    def add_documents(
        self,
        documents: list[str],
    ) -> None:
        """
        Add multiple documents.
        """

        if not isinstance(
            documents,
            list,
        ):
            return

        for document in documents:
            self.add_document(
                document
            )

    # ========================================================
    # SYSTEM CONTEXT
    # ========================================================

    def set_system(
        self,
        system: str,
    ) -> None:
        """
        Replace the system instruction.
        """

        self.system = str(
            system or ""
        ).strip()

    def append_system(
        self,
        system: str,
    ) -> None:
        """
        Append additional system instructions.
        """

        value = str(
            system or ""
        ).strip()

        if not value:
            return

        if self.system:
            self.system = (
                f"{self.system}\n\n{value}"
            )
        else:
            self.system = value

    # ========================================================
    # METADATA
    # ========================================================

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store structured context metadata.
        """

        normalized_key = str(
            key or ""
        ).strip()

        if not normalized_key:
            return

        self.metadata[
            normalized_key
        ] = value

    def update_metadata(
        self,
        values: dict[str, Any],
    ) -> None:
        """
        Merge multiple metadata values.
        """

        if not isinstance(
            values,
            dict,
        ):
            return

        self.metadata.update(
            values
        )

    # ========================================================
    # ACCESSORS
    # ========================================================

    def latest(
        self,
        count: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Return the newest messages.
        """

        if count <= 0:
            return []

        return self.messages[
            -count:
        ]

    def last_message(
        self,
    ) -> dict[str, Any] | None:
        """
        Return the newest message.
        """

        if not self.messages:
            return None

        return self.messages[-1]

    def message_count(
        self,
    ) -> int:
        return len(
            self.messages
        )

    # ========================================================
    # PROMPT SERIALIZATION
    # ========================================================

    def as_prompt(
        self,
        include_system: bool = True,
        include_memories: bool = True,
        include_documents: bool = True,
    ) -> str:
        """
        Convert the context into a model-ready textual prompt.
        """

        sections: list[str] = []

        if include_system and self.system:
            sections.append(
                "SYSTEM:\n"
                + self.system
            )

        if include_memories and self.memories:
            sections.append(
                "MEMORIES:\n"
                + "\n".join(
                    f"- {memory}"
                    for memory in self.memories
                )
            )

        if include_documents and self.documents:
            sections.append(
                "DOCUMENTS:\n"
                + "\n".join(
                    f"- {document}"
                    for document in self.documents
                )
            )

        if self.messages:
            message_text = "\n".join(
                (
                    f"{message.get('role', 'unknown')}: "
                    f"{message.get('content', '')}"
                )
                for message in self.messages
            )

            sections.append(
                "CONVERSATION:\n"
                + message_text
            )

        return "\n\n".join(
            section
            for section in sections
            if section.strip()
        )

    # ========================================================
    # STRUCTURED REPRESENTATION
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Return a serializable representation.
        """

        return {
            "system": self.system,
            "messages": list(
                self.messages
            ),
            "memories": list(
                self.memories
            ),
            "documents": list(
                self.documents
            ),
            "max_items": self.max_items,
            "metadata": dict(
                self.metadata
            ),
        }

    def snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Alias for to_dict(), useful for execution traces.
        """

        return self.to_dict()

    # ========================================================
    # CLONING
    # ========================================================

    def clone(
        self,
    ) -> ContextWindow:
        """
        Create an independent copy of the context window.
        """

        return ContextWindow(
            system=self.system,
            messages=[
                dict(message)
                for message in self.messages
            ],
            memories=list(
                self.memories
            ),
            documents=list(
                self.documents
            ),
            max_items=self.max_items,
            metadata=dict(
                self.metadata
            ),
        )

    # ========================================================
    # CLEARING
    # ========================================================

    def clear_messages(
        self,
    ) -> None:
        """
        Clear conversation messages while preserving the rest
        of the context.
        """

        self.messages.clear()

    def clear_memories(
        self,
    ) -> None:
        self.memories.clear()

    def clear_documents(
        self,
    ) -> None:
        self.documents.clear()

    def clear(
        self,
    ) -> None:
        """
        Clear all dynamic context while preserving the configured
        maximum window size.
        """

        self.system = ""
        self.messages.clear()
        self.memories.clear()
        self.documents.clear()
        self.metadata.clear()

    # ========================================================
    # LENGTH / BOOLEAN SUPPORT
    # ========================================================

    def __len__(
        self,
    ) -> int:
        return self.message_count()

    def __bool__(
        self,
    ) -> bool:
        return bool(
            self.system
            or self.messages
            or self.memories
            or self.documents
            or self.metadata
        )

from __future__ import annotations

from datetime import datetime
from typing import Any


class SharedContext:

    def __init__(self):

        self.data: dict[str, dict] = {}

    def set(
        self,
        key: str,
        value: Any,
        source: str = "unknown",
        agent: str | None = None,
        priority: int = 0,
    ):

        self.data[key] = {
            "value": value,
            "source": source,
            "agent": agent,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
        }

    def get(
        self,
        key: str,
        default=None,
    ):

        item = self.data.get(
            key
        )

        if item is None:
            return default

        return item["value"]

    def get_entry(
        self,
        key: str,
    ):

        return self.data.get(
            key
        )

    def all(self):

        return {
            key: item["value"]
            for key, item in self.data.items()
        }

    def entries(self):

        return dict(
            self.data
        )

    def has(
        self,
        key: str,
    ) -> bool:

        return key in self.data

    def clear(self):

        self.data.clear()
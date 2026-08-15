from app.services.memory_search import (
    search_memories,
)


class MemoryProvider:

    def search(
        self,
        db,
        username: str,
        query: str,
    ):
        return search_memories(
            db,
            username,
            query,
        )
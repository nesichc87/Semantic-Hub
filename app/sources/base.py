from abc import ABC, abstractmethod


class SemanticSource(ABC):

    @abstractmethod
    def can_resolve(self, semantic_id: str) -> bool:
        """Return whether this source can resolve the given semantic ID."""
        pass

    @abstractmethod
    def resolve(self, semantic_id: str):
        """Resolve a semantic ID using this source."""
        pass
    @abstractmethod
    def suggest(self, query: str) -> list[str]:
        """
        Return semantic identifiers matching the search query.
        """
        pass
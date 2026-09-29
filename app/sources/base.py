from abc import ABC, abstractmethod
from app.models.semantic import SemanticConcept


class SemanticSource(ABC):

    @abstractmethod
    def can_resolve(self, semantic_id: str) -> bool:
        """Return whether this source can resolve the given semantic ID."""
        pass

    @abstractmethod
    def resolve(self, semantic_id: str) -> SemanticConcept:
        """Resolve a semantic ID into a concept of the internal semantic model."""
        pass
    @abstractmethod
    def suggest(self, query: str) -> list[str]:
        """
        Return semantic identifiers matching the search query.
        """
        pass
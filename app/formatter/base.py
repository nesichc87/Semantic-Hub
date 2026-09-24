from abc import ABC, abstractmethod

from app.models.semantic import SemanticConcept


class SemanticFormatter(ABC):
    """
    Base interface for converting the internal semantic model
    into an external representation.
    """

    @abstractmethod
    def format(self, concept: SemanticConcept) -> dict:
        pass
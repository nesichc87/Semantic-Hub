from app.models.semantic import SemanticConcept
from app.sources.base import SemanticSource


class MockSemanticSource(SemanticSource):

    def can_resolve(self, semantic_id: str) -> bool:
        return semantic_id.startswith("mock:")

    def resolve(self, semantic_id: str) -> SemanticConcept:
        return SemanticConcept(
            semantic_id=semantic_id,
            source="mock",
            name="Example semantic concept",
        )

    def suggest(self, query: str) -> list[str]:
        """
        Suggest mock semantic identifiers matching the query.
        """

        semantic_id = "mock:Example"

        if query.strip().lower() in semantic_id.lower():
            return [semantic_id]

        return []
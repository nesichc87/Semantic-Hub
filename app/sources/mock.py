from app.sources.base import SemanticSource


class MockSemanticSource(SemanticSource):

    def can_resolve(self, semantic_id: str) -> bool:
        return semantic_id.startswith("mock:")

    def resolve(self, semantic_id: str):
        return {
            "semantic_id": semantic_id,
            "source": "mock",
            "name": "Example semantic concept",
        }
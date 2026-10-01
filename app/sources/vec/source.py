from app.models.semantic import SemanticConcept
from app.sources.base import SemanticSource
from app.sources.vec.mapper import map_vec_class
from app.sources.vec.service import VECService


class VECSemanticSource(SemanticSource):
    """
    Semantic source adapter for VEC.
    """

    def __init__(self, service: VECService):
        self.service = service

    def can_resolve(self, semantic_id: str) -> bool:
        return semantic_id.startswith("vec:")

    def resolve(self, semantic_id: str) -> SemanticConcept:
        result = self.service.get_class(semantic_id)

        return map_vec_class(semantic_id, result)

    def suggest(self, query: str) -> list[str]:
        """
        Suggest VEC semantic identifiers matching the query.
        """
        return self.service.suggest_classes(query)
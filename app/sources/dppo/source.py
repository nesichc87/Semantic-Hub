from app.models.semantic import SemanticConcept
from app.sources.base import SemanticSource
from app.sources.dppo.mapper import map_dppo_class
from app.sources.dppo.service import DPPOService


class DPPOSemanticSource(SemanticSource):
    """
    Semantic source adapter for the Digital Product Passport Ontology
    (DPPO).
    """

    def __init__(self, service: DPPOService):
        self.service = service

    def can_resolve(self, semantic_id: str) -> bool:
        return semantic_id.startswith("dppo:")

    def resolve(self, semantic_id: str) -> SemanticConcept:
        result = self.service.get_class(semantic_id)

        return map_dppo_class(semantic_id, result)

    def suggest(self, query: str) -> list[str]:
        """
        Suggest DPPO semantic identifiers matching the query.
        """
        return self.service.suggest_classes(query)
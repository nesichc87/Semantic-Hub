from app.models.semantic import SemanticConcept
from app.sources.base import SemanticSource
from app.sources.qudt.mapper import map_qudt_unit
from app.sources.qudt.service import QUDTService


UNIT_PREFIX = "qudt:unit:"


class QUDTSemanticSource(SemanticSource):
    """
    Semantic source adapter for QUDT units.
    """

    def __init__(self, service: QUDTService):
        self.service = service

    def can_resolve(self, semantic_id: str) -> bool:
        return semantic_id.startswith(UNIT_PREFIX)

    def resolve(self, semantic_id: str) -> SemanticConcept:
        result = self.service.get_unit(semantic_id)

        return map_qudt_unit(semantic_id, result)

    def suggest(self, query: str) -> list[str]:
        """
        Suggest QUDT unit identifiers matching the query.
        """
        return self.service.suggest_units(query)
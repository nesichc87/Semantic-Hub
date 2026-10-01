from app.models.semantic import SemanticConcept
from app.sources.base import SemanticSource
from app.sources.kbl.mapper import map_kbl_type
from app.sources.kbl.service import KBLService


class KBLSemanticSource(SemanticSource):
    """
    Semantic source adapter for KBL.
    """

    def __init__(self, service: KBLService):
        self.service = service

    def can_resolve(self, semantic_id: str) -> bool:
        return semantic_id.startswith("kbl:")

    def resolve(self, semantic_id: str) -> SemanticConcept:
        result = self.service.get_type(semantic_id)

        return map_kbl_type(semantic_id, result)

        return SemanticConcept(
            semantic_id=semantic_id,
            source="kbl",
            name=semantic_id.split(":", 1)[-1],
            properties=properties,
            provenance={
                "source": "kbl",
                "source_reference": semantic_id,
            },
        )

    def suggest(self, query: str) -> list[str]:
        """
        Suggest KBL semantic identifiers matching the query.
        """
        return self.service.suggest_types(query)
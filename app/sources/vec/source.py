from app.models.semantic import SemanticConcept, SemanticProperty
from app.sources.base import SemanticSource
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

        properties = [
            SemanticProperty(
                semantic_id=prop["semantic_id"],
                name=prop["name"],
                description=prop["description"],
                data_type=prop["data_type"],
                provenance={
                    "source": "vec",
                    "source_reference": prop["semantic_id"],
                },
            )
            for prop in result["properties"]
        ]

        return SemanticConcept(
            semantic_id=semantic_id,
            source="vec",
            name=result["name"],
            description=result["description"],
            properties=properties,
            provenance={
                "source": "vec",
                "source_reference": semantic_id,
            },
        )

    def suggest(self, query: str) -> list[str]:
        """
        Suggest VEC semantic identifiers matching the query.
        """
        return self.service.suggest_classes(query)
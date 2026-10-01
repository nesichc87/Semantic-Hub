from app.formatter.base import SemanticFormatter
from app.models.semantic import SemanticConcept


class OriginalFormatter(SemanticFormatter):
    """
    Returns the semantic concept in a source-oriented representation.

    This formatter is intentionally simple for now. Source-specific
    format preservation will be implemented by the individual
    source adapters where required.
    """

    def format(self, concept: SemanticConcept) -> dict:
        return {
            "semantic_id": concept.semantic_id,
            "source": concept.source,
            "name": concept.name,
            "description": concept.description,
            "data_type": concept.data_type,
            "properties": [
                {
                    "semantic_id": prop.semantic_id,
                    "name": prop.name,
                    "description": prop.description,
                    "data_type": prop.data_type,
                    "unit": prop.unit,
                    "provenance": prop.provenance,
                }
                for prop in concept.properties
            ],
            "provenance": concept.provenance,
        }
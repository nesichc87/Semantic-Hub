from app.formatter.base import SemanticFormatter
from app.formatter.iec61360_types import map_data_type
from app.models.semantic import (
    IEC61360Concept,
    IEC61360Property,
    SemanticConcept,
)


class IEC61360Formatter(SemanticFormatter):
    """
    Converts the internal semantic model into an IEC 61360-oriented
    representation.

    The output model is intentionally minimal and can be extended
    as additional IEC 61360 fields become available.
    """

    def format(self, concept: SemanticConcept) -> IEC61360Concept:
        """
        Convert a normalized semantic concept into an IEC 61360 model.
        """

        properties = [
            IEC61360Property(
                semantic_id=prop.semantic_id,
                preferred_name=prop.name,
                definition=prop.description,
                data_type=map_data_type(prop.data_type),
                unit=prop.unit,
                source_of_definition=prop.provenance.get("source"),
            )
            for prop in concept.properties
        ]

        return IEC61360Concept(
            semantic_id=concept.semantic_id,
            preferred_name=concept.name,
            definition=concept.description,
            source_of_definition=concept.provenance.get("source"),
            properties=properties,
            data_type=map_data_type(concept.data_type),
        )
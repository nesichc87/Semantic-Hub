from app.models.semantic import SemanticConcept


def map_qudt_unit(semantic_id: str, result: dict) -> SemanticConcept:
    """
    Map a resolved QUDT unit to the internal semantic model.

    QUDT units are individuals, not classes. They have no property
    definitions and are not value types, so properties stay empty and
    data_type stays None. Unit values such as symbol or IEC 61360 code
    are not mapped yet.
    """

    return SemanticConcept(
        semantic_id=semantic_id,
        source="qudt",
        name=result["name"],
        description=result["description"],
        provenance={
            "source": "qudt",
            "source_reference": semantic_id,
        },
    )
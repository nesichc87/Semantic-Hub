from app.models.semantic import SemanticConcept, SemanticProperty


def map_kbl_type(semantic_id: str, result: dict) -> SemanticConcept:
    """
    Map a resolved KBL type to the internal semantic model.
    """

    properties = [
        SemanticProperty(
            semantic_id=f"{semantic_id}:{element['name']}",
            name=element["name"],
            data_type=element["type"],
            provenance={
                "source": "kbl",
                "source_reference": semantic_id,
            },
        )
        for element in result["elements"]
    ]

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
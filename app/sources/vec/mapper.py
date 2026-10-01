from app.models.semantic import SemanticConcept, SemanticProperty


def map_vec_class(semantic_id: str, result: dict) -> SemanticConcept:
    """
    Map a resolved VEC class to the internal semantic model.
    """

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
from app.models.semantic import SemanticConcept, SemanticProperty


def map_dppo_class(semantic_id: str, result: dict) -> SemanticConcept:
    """
    Map a resolved DPPO class to the internal semantic model.
    """

    properties = [
        SemanticProperty(
            semantic_id=prop["semantic_id"],
            name=prop["name"],
            description=prop["description"],
            data_type=prop["data_type"],
            provenance={
                "source": "dppo",
                "source_reference": prop["semantic_id"],
            },
        )
        for prop in result["properties"]
    ]

    return SemanticConcept(
        semantic_id=semantic_id,
        source="dppo",
        name=result["name"],
        description=result["description"],
        properties=properties,
        provenance={
            "source": "dppo",
            "source_reference": semantic_id,
        },
    )
from app.models.semantic import SemanticConcept, SemanticProperty


def map_kbl_type(semantic_id: str, result: dict) -> SemanticConcept:
    """
    Map a resolved KBL type to the internal semantic model.

    Complex types are mapped to a concept with properties. Simple and
    built-in types have no properties; their (base) data type is kept
    as the concept's data type.
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
        for element in result.get("elements", [])
    ]

    if result["kind"] == "simple":
        data_type = result["base_type"]
    elif result["kind"] == "builtin":
        data_type = result["type"]
    else:
        data_type = None

    return SemanticConcept(
        semantic_id=semantic_id,
        source="kbl",
        name=semantic_id.split(":", 1)[-1],
        properties=properties,
        provenance={
            "source": "kbl",
            "source_reference": semantic_id,
        },
        data_type=data_type,
    )
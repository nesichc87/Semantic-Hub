from dataclasses import dataclass, field


@dataclass
class SemanticProperty:
    """
    A normalized semantic property independent of the source system.
    """

    semantic_id: str
    name: str
    description: str | None = None
    data_type: str | None = None
    unit: str | None = None

    provenance: dict[str, str] = field(default_factory=dict)


@dataclass
class SemanticConcept:
    """
    A normalized semantic concept independent of the source system.
    """

    semantic_id: str
    source: str
    name: str
    description: str | None = None

    properties: list[SemanticProperty] = field(default_factory=list)

    provenance: dict[str, str] = field(default_factory=dict)


@dataclass
class IEC61360Property:
    """
    IEC 61360-oriented representation of a semantic property.

    This is an output model and is separate from the internal
    source-independent SemanticProperty model.
    """

    semantic_id: str
    preferred_name: str
    definition: str | None = None
    data_type: str | None = None
    unit: str | None = None
    source_of_definition: str | None = None


@dataclass
class IEC61360Concept:
    """
    IEC 61360-oriented representation of a semantic concept.

    The model is intentionally minimal and can be extended as
    additional IEC 61360 fields and source metadata become available.
    """

    semantic_id: str
    preferred_name: str
    definition: str | None = None
    source_of_definition: str | None = None

    properties: list[IEC61360Property] = field(default_factory=list)
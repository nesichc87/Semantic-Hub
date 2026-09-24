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
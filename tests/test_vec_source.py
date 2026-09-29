import pytest

from app.models.semantic import SemanticConcept
from app.sources.vec.source import VECSemanticSource


class FakeVECService:
    def get_class(self, semantic_id: str) -> dict:
        if semantic_id != "vec:PartVersion":
            raise ValueError(f"VEC class '{semantic_id}' not found")

        return {
            "name": "PartVersion",
            "description": "Identifies a part.",
            "properties": [
                {
                    "semantic_id": "vec:partVersionPartNumber",
                    "name": "partVersionPartNumber",
                    "description": "The part number.",
                    "data_type": "xs:string",
                },
            ],
        }

    def suggest_classes(self, query: str) -> list[str]:
        return ["vec:PartVersion"]


def test_can_resolve_only_vec_identifiers():
    source = VECSemanticSource(FakeVECService())

    assert source.can_resolve("vec:PartVersion") is True
    assert source.can_resolve("kbl:Component") is False


def test_resolve_returns_semantic_concept():
    source = VECSemanticSource(FakeVECService())

    concept = source.resolve("vec:PartVersion")

    assert isinstance(concept, SemanticConcept)
    assert concept.semantic_id == "vec:PartVersion"
    assert concept.source == "vec"
    assert concept.name == "PartVersion"
    assert concept.description == "Identifies a part."
    assert concept.provenance == {
        "source": "vec",
        "source_reference": "vec:PartVersion",
    }

    assert len(concept.properties) == 1

    prop = concept.properties[0]

    assert prop.semantic_id == "vec:partVersionPartNumber"
    assert prop.name == "partVersionPartNumber"
    assert prop.description == "The part number."
    assert prop.data_type == "xs:string"
    assert prop.unit is None
    assert prop.provenance == {
        "source": "vec",
        "source_reference": "vec:partVersionPartNumber",
    }


def test_resolve_unknown_class_raises_value_error():
    source = VECSemanticSource(FakeVECService())

    with pytest.raises(ValueError):
        source.resolve("vec:DoesNotExist")


def test_suggest_delegates_to_service():
    source = VECSemanticSource(FakeVECService())

    assert source.suggest("part") == ["vec:PartVersion"]
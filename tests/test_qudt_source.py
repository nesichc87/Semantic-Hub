import pytest

from app.models.semantic import SemanticConcept
from app.sources.qudt.source import QUDTSemanticSource


class FakeQUDTService:
    def get_unit(self, semantic_id: str) -> dict:
        if semantic_id != "qudt:unit:M":
            raise ValueError(f"QUDT unit '{semantic_id}' not found")

        return {
            "name": "Metre",
            "description": "The SI base unit of distance.",
        }

    def suggest_units(self, query: str) -> list[str]:
        return ["qudt:unit:M"]


def test_can_resolve_only_qudt_unit_identifiers():
    source = QUDTSemanticSource(FakeQUDTService())

    assert source.can_resolve("qudt:unit:M") is True
    assert source.can_resolve("qudt:quantitykind:Length") is False
    assert source.can_resolve("vec:PartVersion") is False


def test_resolve_returns_semantic_concept():
    source = QUDTSemanticSource(FakeQUDTService())

    concept = source.resolve("qudt:unit:M")

    assert isinstance(concept, SemanticConcept)
    assert concept.semantic_id == "qudt:unit:M"
    assert concept.source == "qudt"
    assert concept.name == "Metre"
    assert concept.description == "The SI base unit of distance."
    assert concept.properties == []
    assert concept.provenance == {
        "source": "qudt",
        "source_reference": "qudt:unit:M",
    }


def test_resolve_unknown_unit_raises_value_error():
    source = QUDTSemanticSource(FakeQUDTService())

    with pytest.raises(ValueError):
        source.resolve("qudt:unit:DoesNotExist")


def test_suggest_delegates_to_service():
    source = QUDTSemanticSource(FakeQUDTService())

    assert source.suggest("metre") == ["qudt:unit:M"]
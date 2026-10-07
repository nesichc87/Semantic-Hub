import pytest

from app.sources.qudt.service import QUDTService


TTL = b"""
@prefix unit: <http://qudt.org/vocab/unit/> .
@prefix qudt: <http://qudt.org/schema/qudt/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

unit:M a qudt:Unit ;
    rdfs:label "Meter"@de , "Meter"@en-US , "Metre"@en ;
    qudt:plainTextDescription "The SI base unit of distance." ;
    dcterms:description "The SI base unit of distance, $c$." .

unit:FT a qudt:Unit ;
    rdfs:label "Foot"@en ;
    dcterms:description "An imperial unit of length." .

unit:NoDescription a qudt:Unit ;
    rdfs:label "No description"@en .
unit:GermanOnly a qudt:Unit ;
    rdfs:label "Nur Deutsch"@de .
"""


class FakeClient:
    def __init__(self, ttl: bytes = TTL):
        self.ttl = ttl

    def get_ttl(self) -> bytes:
        return self.ttl


def test_get_unit_prefers_english_label_and_plain_text_description():
    service = QUDTService(client=FakeClient())

    result = service.get_unit("qudt:unit:M")

    assert result == {
        "name": "Metre",
        "description": "The SI base unit of distance.",
    }


def test_get_unit_falls_back_to_dcterms_description():
    service = QUDTService(client=FakeClient())

    result = service.get_unit("qudt:unit:FT")

    assert result["description"] == "An imperial unit of length."


def test_get_unit_without_description_returns_none():
    service = QUDTService(client=FakeClient())

    result = service.get_unit("qudt:unit:NoDescription")

    assert result["description"] is None


@pytest.mark.parametrize(
    "semantic_id",
    ["qudt:unit:DoesNotExist", "qudt:unit:m", "vec:M", "unit:M"],
)
def test_get_unit_raises_for_unknown_or_foreign_id(semantic_id):
    service = QUDTService(client=FakeClient())

    with pytest.raises(ValueError):
        service.get_unit(semantic_id)
def test_get_unit_falls_back_to_local_name_without_english_label():
    service = QUDTService(client=FakeClient())

    result = service.get_unit("qudt:unit:GermanOnly")

    assert result["name"] == "GermanOnly"
def test_suggest_units_matches_english_label_case_insensitive():
    service = QUDTService(client=FakeClient())

    assert service.suggest_units("METRE") == ["qudt:unit:M"]
    assert service.suggest_units("  foot  ") == ["qudt:unit:FT"]


def test_suggest_units_matches_local_name_without_duplicates():
    service = QUDTService(client=FakeClient())

    assert service.suggest_units("m") == [
        "qudt:unit:GermanOnly",
        "qudt:unit:M",
    ]


def test_suggest_units_ignores_non_english_labels():
    service = QUDTService(client=FakeClient())

    assert service.suggest_units("deutsch") == []
    assert service.suggest_units("meter") == []


def test_suggest_units_returns_empty_list_for_blank_query():
    service = QUDTService(client=FakeClient())

    assert service.suggest_units("   ") == []
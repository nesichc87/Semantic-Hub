import pytest

from app.sources.vec.service import VECService


TTL = b"""
@prefix vec: <http://www.prostep.org/ontologies/ecad/2024/03/vec#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

vec:PartVersion a owl:Class ;
    rdfs:comment "Identifies a part." .

vec:partVersionPartNumber a owl:DatatypeProperty ;
    rdfs:domain vec:PartVersion ;
    rdfs:range xsd:string ;
    rdfs:comment "The part number." .

vec:partVersionAliasId a owl:ObjectProperty ;
    rdfs:domain vec:PartVersion ;
    rdfs:range vec:AliasIdentification ;
    rdfs:comment "Alias identifications of the part." .
"""


class FakeClient:
    def __init__(self, ttl: bytes = TTL):
        self.ttl = ttl

    def get_ttl(self) -> bytes:
        return self.ttl


def test_get_class_returns_direct_properties():
    service = VECService(client=FakeClient())

    result = service.get_class("vec:PartVersion")

    assert result["name"] == "PartVersion"
    assert result["description"] == "Identifies a part."
    assert result["properties"] == [
        {
            "semantic_id": "vec:partVersionAliasId",
            "name": "partVersionAliasId",
            "description": "Alias identifications of the part.",
            "data_type": "vec:AliasIdentification",
        },
        {
            "semantic_id": "vec:partVersionPartNumber",
            "name": "partVersionPartNumber",
            "description": "The part number.",
            "data_type": "xs:string",
        },
    ]


def test_get_class_raises_for_unknown_class():
    service = VECService(client=FakeClient())

    with pytest.raises(ValueError):
        service.get_class("vec:DoesNotExist")

TTL_WITH_INHERITANCE = b"""
@prefix vec: <http://www.prostep.org/ontologies/ecad/2024/03/vec#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

vec:ExtendableElement a owl:Class .

vec:extendableElementCustomProperty a owl:ObjectProperty ;
    rdfs:domain vec:ExtendableElement ;
    rdfs:range vec:CustomProperty .

vec:ItemVersion a owl:Class ;
    rdfs:subClassOf vec:ExtendableElement .

vec:itemVersionCompanyName a owl:DatatypeProperty ;
    rdfs:domain vec:ItemVersion ;
    rdfs:range xsd:string .

vec:PartVersion a owl:Class ;
    rdfs:subClassOf vec:ItemVersion ,
        [ a owl:Restriction ;
          owl:onProperty vec:partVersionPartNumber ;
          owl:maxCardinality 1 ] .

vec:partVersionPartNumber a owl:DatatypeProperty ;
    rdfs:domain vec:PartVersion ;
    rdfs:range xsd:string .
"""


def test_get_class_includes_inherited_properties_base_first():
    service = VECService(client=FakeClient(TTL_WITH_INHERITANCE))

    result = service.get_class("vec:PartVersion")

    assert [p["semantic_id"] for p in result["properties"]] == [
        "vec:extendableElementCustomProperty",
        "vec:itemVersionCompanyName",
        "vec:partVersionPartNumber",
    ]

def test_suggest_classes_matches_case_insensitive_substring():
    service = VECService(client=FakeClient(TTL_WITH_INHERITANCE))

    assert service.suggest_classes("version") == [
        "vec:ItemVersion",
        "vec:PartVersion",
    ]
    assert service.suggest_classes("PART") == ["vec:PartVersion"]
    assert service.suggest_classes("  part  ") == ["vec:PartVersion"]


def test_suggest_classes_returns_empty_list_without_match():
    service = VECService(client=FakeClient(TTL_WITH_INHERITANCE))

    assert service.suggest_classes("Wire") == []
    assert service.suggest_classes("   ") == []
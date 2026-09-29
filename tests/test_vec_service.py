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
    def get_ttl(self) -> bytes:
        return TTL


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
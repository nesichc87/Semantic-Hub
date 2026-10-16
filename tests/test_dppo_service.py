import pytest

from app.sources.dppo.service import DPPO_MODULES, DPPOService


PREFIXES = """
@prefix odp: <http://w3id.org/dppo/ontology/dpp-odp/> .
@prefix core: <http://w3id.org/dppo/ontology/dpp-core/> .
@prefix info: <http://w3id.org/dppo/ontology/dpp-info/> .
@prefix prov: <http://w3id.org/dppo/ontology/dpp-prov/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""

MODULE_TTL = {
    "dpp-odp": PREFIXES + """
odp:DPP a owl:Class ;
    rdfs:label "Digital Product Passport"@en ;
    rdfs:comment "A digital product passport."@en .

odp:Product a owl:Class .

odp:describes a owl:ObjectProperty ;
    rdfs:domain odp:DPP ;
    rdfs:range odp:Product ;
    rdfs:comment "Links a DPP to its product."@en .
""",
    "dpp-core": PREFIXES + """
core:ComponentDPP a owl:Class ;
    rdfs:subClassOf odp:DPP ;
    rdfs:label "Component DPP"@en ;
    rdfs:comment "A DPP for a component."@en .
""",
    "dpp-info": PREFIXES + """
info:CompositionInformation a owl:Class .

<http://w3id.org/dppo/ontology/dpp-info/0.1/CompositionInformation> a owl:Class .
""",
    "dpp-prov": PREFIXES + """
prov:creationTimeStamp a owl:DatatypeProperty ;
    rdfs:domain core:ComponentDPP ;
    rdfs:range xsd:dateTime .

prov:dppOwner a owl:ObjectProperty ;
    rdfs:domain [ a owl:Class ; owl:unionOf ( odp:DPP core:ComponentDPP ) ] .
""",
}


class FakeClient:
    def __init__(self, ttl_by_module: dict[str, str] = MODULE_TTL):
        self.ttl_by_module = ttl_by_module
        self.calls = []

    def get_ttl(self, module: str) -> bytes:
        self.calls.append(module)
        return self.ttl_by_module.get(module, "").encode("utf-8")


class FailingOnceClient(FakeClient):
    def get_ttl(self, module: str) -> bytes:
        if not self.calls:
            self.calls.append(module)
            raise RuntimeError("source not reachable")

        return super().get_ttl(module)


def test_get_class_returns_local_name_comment_and_properties_across_modules():
    service = DPPOService(client=FakeClient())

    result = service.get_class("dppo:dpp-core:ComponentDPP")

    assert result["name"] == "ComponentDPP"
    assert result["description"] == "A DPP for a component."
    assert result["properties"] == [
        {
            "semantic_id": "dppo:dpp-odp:describes",
            "name": "describes",
            "description": "Links a DPP to its product.",
            "data_type": "dppo:dpp-odp:Product",
        },
        {
            "semantic_id": "dppo:dpp-prov:creationTimeStamp",
            "name": "creationTimeStamp",
            "description": None,
            "data_type": "xs:dateTime",
        },
    ]


@pytest.mark.parametrize(
    "semantic_id",
    [
        "dppo:dpp-core:DoesNotExist",
        "dppo:dpp-unknown:DPP",
        "dppo:DPP",
        "dppo:dpp-info:0.1/CompositionInformation",
        "vec:PartVersion",
    ],
)
def test_get_class_raises_for_invalid_or_unknown_ids(semantic_id):
    service = DPPOService(client=FakeClient())

    with pytest.raises(ValueError):
        service.get_class(semantic_id)


def test_suggest_classes_uses_local_names_and_skips_versioned_iris():
    service = DPPOService(client=FakeClient())

    assert service.suggest_classes("composition") == [
        "dppo:dpp-info:CompositionInformation",
    ]
    assert service.suggest_classes("dpp") == [
        "dppo:dpp-odp:DPP",
        "dppo:dpp-core:ComponentDPP",
    ]


def test_suggest_classes_returns_empty_list_for_blank_query():
    client = FakeClient()
    service = DPPOService(client=client)

    assert service.suggest_classes("   ") == []
    assert client.calls == []


def test_modules_are_loaded_once():
    client = FakeClient()
    service = DPPOService(client=client)

    service.get_class("dppo:dpp-core:ComponentDPP")
    service.suggest_classes("dpp")

    assert sorted(client.calls) == sorted(DPPO_MODULES)


def test_failed_load_is_not_cached():
    client = FailingOnceClient()
    service = DPPOService(client=client)

    with pytest.raises(RuntimeError):
        service.get_class("dppo:dpp-core:ComponentDPP")

    assert service.get_class("dppo:dpp-core:ComponentDPP")["name"] == "ComponentDPP"
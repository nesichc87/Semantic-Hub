import pytest

from app.sources.generic.config_schema import RDFSourceConfig
from app.sources.generic.rdf import GenericRDFSource


TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <https://example.org/vocab/> .
@prefix t: <https://example.org/types/> .

ex:Metre a t:Unit ;
    rdfs:label "metre"@en, "Meter"@de ;
    rdfs:comment "Length   unit\\n  of the SI."@en .

ex:Thing a t:Other ;
    rdfs:label "thing"@en .
"""

LOCATION = "https://example.org/vocab.ttl"


class FakeFetch:
    def __init__(self, data: bytes, failures: int = 0):
        self.data = data
        self.failures = failures
        self.calls = []

    def __call__(self, location: str, fmt: str) -> bytes:
        self.calls.append((location, fmt))
        if self.failures:
            self.failures -= 1
            raise RuntimeError("source unavailable")
        return self.data


def make_source(fetch, **overrides):
    raw = {
        "id": "example",
        "prefix": "ex:",
        "namespace": "https://example.org/vocab/",
        "locations": [LOCATION],
        "format": "turtle",
        "prefixes": {
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "t": "https://example.org/types/",
        },
        "types": ["t:Unit"],
        "label": ["rdfs:label"],
        "description": ["rdfs:comment"],
    }
    raw.update(overrides)
    return GenericRDFSource(RDFSourceConfig.model_validate(raw), fetch)


def test_resolves_concept_with_english_label_and_normalized_description():
    concept = make_source(FakeFetch(TTL)).resolve("ex:Metre")

    assert concept.semantic_id == "ex:Metre"
    assert concept.source == "example"
    assert concept.name == "metre"
    assert concept.description == "Length unit of the SI."
    assert concept.properties == []
    assert concept.data_type is None
    assert concept.provenance == {"source": "example", "source_reference": "ex:Metre"}


def test_resolve_is_case_sensitive():
    with pytest.raises(ValueError):
        make_source(FakeFetch(TTL)).resolve("ex:metre")


def test_resolve_ignores_subjects_of_other_types():
    with pytest.raises(ValueError):
        make_source(FakeFetch(TTL)).resolve("ex:Thing")


def test_can_resolve_checks_prefix_only():
    source = make_source(FakeFetch(TTL))

    assert source.can_resolve("ex:Anything")
    assert not source.can_resolve("other:Metre")


def test_loads_once_and_passes_format_to_fetch():
    fetch = FakeFetch(TTL)
    source = make_source(fetch)

    source.resolve("ex:Metre")
    source.resolve("ex:Metre")

    assert fetch.calls == [(LOCATION, "turtle")]


def test_failed_load_is_not_cached():
    fetch = FakeFetch(TTL, failures=1)
    source = make_source(fetch)

    with pytest.raises(RuntimeError):
        source.resolve("ex:Metre")

    assert source.resolve("ex:Metre").name == "metre"
    assert len(fetch.calls) == 2

SUGGEST_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <https://example.org/vocab/> .
@prefix t: <https://example.org/types/> .

ex:Kilogram a t:Unit ; rdfs:label "kilogram"@en .
ex:Gram a t:Unit ; rdfs:label "gram"@en .
ex:Metre a t:Unit ; rdfs:label "metre"@en, "Meter"@de .
ex:Thing a t:Other ; rdfs:label "thing"@en .
"""


def test_suggest_ranks_exact_before_substring():
    source = make_source(FakeFetch(SUGGEST_TTL))

    assert source.suggest("gram") == ["ex:Gram", "ex:Kilogram"]


def test_suggest_ignores_labels_in_other_languages():
    source = make_source(FakeFetch(SUGGEST_TTL))

    assert source.suggest("meter") == []


def test_suggest_ignores_subjects_of_other_types():
    source = make_source(FakeFetch(SUGGEST_TTL))

    assert source.suggest("thing") == []


def test_suggest_with_empty_query_does_not_load():
    fetch = FakeFetch(SUGGEST_TTL)

    assert make_source(fetch).suggest("") == []
    assert fetch.calls == []

NAMES_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <https://example.org/vocab/> .
@prefix t: <https://example.org/types/> .

ex:Metre a t:Unit ; rdfs:label "meter"@en .
ex:Gram a t:Unit ; rdfs:label "Gramm"@de .
ex:Second a t:Unit .
"""


def test_name_from_label_falls_back_to_local_name():
    source = make_source(FakeFetch(NAMES_TTL))

    assert source.resolve("ex:Gram").name == "Gram"
    with pytest.raises(ValueError):
        source.resolve("ex:Second")


def test_name_from_label_or_local_keeps_concepts_without_label():
    source = make_source(FakeFetch(NAMES_TTL), name_from="label_or_local")

    assert source.resolve("ex:Second").name == "Second"
    assert source.resolve("ex:Metre").name == "meter"


def test_name_from_local_name_ignores_labels():
    source = make_source(FakeFetch(NAMES_TTL), name_from="local_name")

    assert source.resolve("ex:Metre").name == "Metre"
    assert source.suggest("meter") == []


DPPO_LIKE_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix core: <https://example.org/onto/core/> .

core:ComponentDPP a owl:Class ; rdfs:label "Component DPP"@en .
"""


def test_id_separators_map_iri_path_to_semantic_id():
    source = make_source(
        FakeFetch(DPPO_LIKE_TTL),
        prefix="dppo:",
        namespace="https://example.org/onto/",
        prefixes={
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl#",
        },
        types=["owl:Class"],
        id_separators={"/": ":"},
    )

    assert source.resolve("dppo:core:ComponentDPP").name == "Component DPP"
    assert source.suggest("component") == ["dppo:core:ComponentDPP"]

EQUIVALENCE_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ex: <https://example.org/vocab/> .
@prefix t: <https://example.org/types/> .
@prefix q: <https://example.org/schema/> .

ex:Metre a t:Unit ; rdfs:label "metre"@en ;
    owl:sameAs <https://other.example/m> ;
    q:ucumCode "m" .
ex:Gram a t:Unit ; rdfs:label "gram"@en ;
    q:ucumCode "  g  " , "" .
ex:Second a t:Unit ; rdfs:label "second"@en .
<https://other.example/s> skos:exactMatch ex:Second .
ex:Thing a t:Other ; rdfs:label "thing"@en ;
    owl:sameAs <https://other.example/thing> .
"""


def equivalence_source():
    return make_source(
        FakeFetch(EQUIVALENCE_TTL),
        prefixes={
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl#",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "t": "https://example.org/types/",
            "q": "https://example.org/schema/",
        },
        equivalence=["owl:sameAs", "skos:exactMatch"],
        code_links={"q:ucumCode": "ucum:"},
    )


def test_equivalents_from_predicates_in_both_directions_and_codes():
    assert equivalence_source().equivalents() == {
        "ex:Metre": {"https://other.example/m", "ucum:m"},
        "ex:Gram": {"ucum:g"},
        "ex:Second": {"https://other.example/s"},
    }


def test_equivalents_empty_without_configuration():
    assert make_source(FakeFetch(EQUIVALENCE_TTL)).equivalents() == {}

PROPERTIES_TTL = b"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <https://example.org/vocab/> .

ex:Item a owl:Class ; rdfs:label "Item"@en ;
    rdfs:subClassOf ex:Part .
ex:Part a owl:Class ; rdfs:label "Part"@en ;
    rdfs:subClassOf ex:Item , [ a owl:Restriction ] .
ex:Mass a owl:Class ; rdfs:label "Mass"@en .

ex:number rdfs:domain ex:Item ; rdfs:range xsd:string ;
    rdfs:comment "Number."@en .
ex:mass rdfs:domain ex:Part ; rdfs:range ex:Mass .
ex:alias rdfs:domain ex:Part ; rdfs:range <https://elsewhere.example/Alias> .
"""


def test_properties_inherited_first_with_compacted_ids_and_types():
    source = make_source(
        FakeFetch(PROPERTIES_TTL),
        prefixes={
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl#",
        },
        types=["owl:Class"],
        compact={"http://www.w3.org/2001/XMLSchema#": "xs:"},
        properties={
            "domain": "rdfs:domain",
            "superclass": "rdfs:subClassOf",
            "range": "rdfs:range",
            "description": "rdfs:comment",
        },
    )

    properties = source.resolve("ex:Part").properties

    assert [
        (p.semantic_id, p.name, p.description, p.data_type) for p in properties
    ] == [
        ("ex:number", "number", "Number.", "xs:string"),
        ("ex:alias", "alias", None, "https://elsewhere.example/Alias"),
        ("ex:mass", "mass", None, "ex:Mass"),
    ]
    assert properties[0].unit is None
    assert properties[0].provenance == {"source": "example", "source_reference": "ex:number"}
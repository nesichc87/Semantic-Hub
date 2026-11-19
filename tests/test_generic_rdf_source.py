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


def make_source(fetch):
    config = RDFSourceConfig.model_validate(
        {
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
    )
    return GenericRDFSource(config, fetch)


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
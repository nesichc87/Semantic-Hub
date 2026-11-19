import pytest

from app.sources.generic.factory import create_source
from app.sources.generic.rdf import GenericRDFSource


RDF_CONFIG = {
    "id": "example",
    "prefix": "ex:",
    "namespace": "https://example.org/vocab/",
    "locations": ["https://example.org/vocab.ttl"],
    "format": "turtle",
}


def no_fetch(location: str, fmt: str) -> bytes:
    raise AssertionError("The factory must not load the source")


def test_creates_rdf_source_without_loading():
    source = create_source({"type": "rdf", "config": RDF_CONFIG}, no_fetch)

    assert isinstance(source, GenericRDFSource)
    assert source.config.id == "example"
    assert source.can_resolve("ex:Anything")


@pytest.mark.parametrize(
    "entry",
    [
        {"type": "sparql", "config": RDF_CONFIG},
        {"config": RDF_CONFIG},
        {"type": "rdf"},
        {"type": "rdf", "config": {**RDF_CONFIG, "prefix": ""}},
    ],
)
def test_rejects_invalid_entry(entry):
    with pytest.raises(ValueError):
        create_source(entry, no_fetch)
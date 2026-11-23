import pytest

from app.sources.generic.factory import create_source
from app.sources.generic.rdf import GenericRDFSource
from app.sources.generic.table import GenericTableSource
from app.sources.generic.xsd import GenericXSDSource


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

XSD_CONFIG = {
    "id": "kbl",
    "prefix": "kbl:",
    "location": "https://example.org/kbl.xsd",
}


def test_creates_xsd_source_without_loading():
    source = create_source({"type": "xsd", "config": XSD_CONFIG}, no_fetch)

    assert isinstance(source, GenericXSDSource)
    assert source.config.id == "kbl"
    assert source.can_resolve("kbl:Anything")


def test_rejects_rdf_config_for_xsd_type():
    with pytest.raises(ValueError):
        create_source({"type": "xsd", "config": RDF_CONFIG}, no_fetch)


TABLE_CONFIG = {
    "id": "ucum",
    "prefix": "ucum:",
    "location": "https://example.org/ucum.xlsx",
    "format": "xlsx",
    "columns": {"id": "UCUM_CODE"},
}


def test_creates_table_source_without_loading():
    source = create_source({"type": "table", "config": TABLE_CONFIG}, no_fetch)

    assert isinstance(source, GenericTableSource)
    assert source.config.id == "ucum"
    assert source.can_resolve("ucum:mg/dL")


def test_rejects_xsd_config_for_table_type():
    with pytest.raises(ValueError, match="validation error"):
        create_source({"type": "table", "config": XSD_CONFIG}, no_fetch)
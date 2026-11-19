import pytest
from pydantic import ValidationError

from app.sources.generic.config_schema import RDFSourceConfig


def qudt_like_config(**overrides):
    config = {
        "id": "qudt-units",
        "prefix": "qudt:unit:",
        "namespace": "http://qudt.org/vocab/unit/",
        "locations": ["https://qudt.org/vocab/unit/"],
        "format": "turtle",
        "license": "CC BY 4.0",
        "prefixes": {
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "qudt": "http://qudt.org/schema/qudt/",
        },
        "types": ["http://qudt.org/schema/qudt/Unit"],
        "label": ["rdfs:label"],
        "description": ["qudt:plainTextDescription"],
    }
    config.update(overrides)
    return config


def test_accepts_qudt_like_config_with_defaults():
    config = RDFSourceConfig.model_validate(qudt_like_config())

    assert config.prefix == "qudt:unit:"
    assert config.locations == ["https://qudt.org/vocab/unit/"]
    assert config.languages == ["en", None]
    assert config.equivalence == []
    assert config.code_links == {}


def test_rejects_config_without_prefix():
    raw = qudt_like_config()
    del raw["prefix"]

    with pytest.raises(ValidationError):
        RDFSourceConfig.model_validate(raw)


def test_rejects_unknown_option():
    with pytest.raises(ValidationError):
        RDFSourceConfig.model_validate(
            qudt_like_config(description_query="?s ?p ?v")
        )

RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"


def test_expands_prefixed_name():
    config = RDFSourceConfig.model_validate(qudt_like_config())

    assert config.expand("rdfs:label") == RDFS_LABEL


def test_keeps_full_iri():
    config = RDFSourceConfig.model_validate(qudt_like_config())

    assert config.expand(RDFS_LABEL) == RDFS_LABEL


@pytest.mark.parametrize(
    "overrides",
    [
        {"label": ["skos:prefLabel"]},
        {"description": ["label"]},
        {"types": ["qudt"]},
        {"equivalence": ["owl:sameAs"]},
        {"code_links": {"qudt:ucumCode": "ucum:", "dcterms:identifier": "x:"}},
        {
            "properties": {
                "domain": "rdfs:domain",
                "superclass": "rdfs:subClassOf",
                "range": "rdfs:range",
                "description": "skos:definition",
            }
        },
    ],
)
def test_rejects_unresolvable_predicate(overrides):
    with pytest.raises(ValidationError):
        RDFSourceConfig.model_validate(qudt_like_config(**overrides))
import json

import pytest
from sqlalchemy import create_engine

from app.catalog.db import upgrade_database
from app.catalog.repository import CatalogConflictError, SourceCatalog
from app.catalog.seed import DEFAULT_SEED_PATH, activate_seed, load_seed, preselect_seed


@pytest.fixture
def catalog(catalog_url):
    upgrade_database(catalog_url)
    engine = create_engine(catalog_url)
    yield SourceCatalog(engine)
    engine.dispose()


def rdf_entry(source_id, prefix):
    return {
        "type": "rdf",
        "config": {
            "id": source_id,
            "prefix": prefix,
            "namespace": f"https://example.org/{source_id}/",
            "locations": [f"https://example.org/{source_id}.ttl"],
            "format": "turtle",
        },
    }


SEED = [
    {
        "id": "example",
        "description": "Example vocabulary for tests",
        "license": "CC BY 4.0",
        "entry": rdf_entry("example", "ex:"),
    },
    {
        "id": "units",
        "description": "Units for tests",
        "license": "MIT",
        "entry": rdf_entry("units", "u:"),
    },
]


def write_seed(tmp_path, data) -> str:
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_seed_reads_entries(tmp_path):
    seeds = load_seed(write_seed(tmp_path, SEED))

    assert [seed.id for seed in seeds] == ["example", "units"]
    assert seeds[0].description == "Example vocabulary for tests"
    assert seeds[0].license == "CC BY 4.0"
    assert seeds[0].entry == SEED[0]["entry"]


@pytest.mark.parametrize(
    "data",
    [
        [{**SEED[0], "id": "other"}],
        [SEED[0], SEED[0]],
        [{key: value for key, value in SEED[0].items() if key != "license"}],
        [{**SEED[0], "extra": "x"}],
    ],
)
def test_load_seed_rejects_invalid_file(tmp_path, data):
    with pytest.raises(ValueError):
        load_seed(write_seed(tmp_path, data))


def test_shipped_seed_file_is_empty_for_now():
    assert load_seed(DEFAULT_SEED_PATH) == []


def test_activate_requires_license_confirmation(tmp_path, catalog):
    seeds = load_seed(write_seed(tmp_path, SEED))

    with pytest.raises(ValueError):
        activate_seed(catalog, seeds, "units", license_confirmed=False)
    assert catalog.list_sources() == []


def test_activate_stores_approved_source_with_seed_license(tmp_path, catalog):
    seeds = load_seed(write_seed(tmp_path, SEED))

    record = activate_seed(catalog, seeds, "units", license_confirmed=True)

    assert record.status == "approved"
    assert record.license == "MIT"
    assert record.config == SEED[1]["entry"]["config"]


def test_activate_unknown_or_already_active_seed(tmp_path, catalog):
    seeds = load_seed(write_seed(tmp_path, SEED))
    activate_seed(catalog, seeds, "units", license_confirmed=True)

    with pytest.raises(ValueError):
        activate_seed(catalog, seeds, "missing", license_confirmed=True)
    with pytest.raises(CatalogConflictError):
        activate_seed(catalog, seeds, "units", license_confirmed=True)


def test_preselect_activates_listed_seeds_on_empty_catalog(tmp_path, catalog):
    seeds = load_seed(write_seed(tmp_path, SEED))

    activated = preselect_seed(catalog, seeds, {"SEMANTIC_HUB_SEED_SOURCES": "units, example"})

    assert activated == ["units", "example"]
    assert {record.id: record.status for record in catalog.list_sources()} == {
        "units": "approved",
        "example": "approved",
    }


def test_preselect_does_nothing_if_catalog_is_not_empty(tmp_path, catalog):
    seeds = load_seed(write_seed(tmp_path, SEED))
    catalog.add(rdf_entry("own", "own:"))

    activated = preselect_seed(catalog, seeds, {"SEMANTIC_HUB_SEED_SOURCES": "units"})

    assert activated == []
    assert [record.id for record in catalog.list_sources()] == ["own"]


@pytest.mark.parametrize("environ", [{}, {"SEMANTIC_HUB_SEED_SOURCES": ""}])
def test_preselect_without_variable_does_nothing(tmp_path, catalog, environ):
    seeds = load_seed(write_seed(tmp_path, SEED))

    assert preselect_seed(catalog, seeds, environ) == []
    assert catalog.list_sources() == []


def test_preselect_with_unknown_id_activates_nothing(tmp_path, catalog):
    seeds = load_seed(write_seed(tmp_path, SEED))

    with pytest.raises(ValueError):
        preselect_seed(catalog, seeds, {"SEMANTIC_HUB_SEED_SOURCES": "units, missing"})
    assert catalog.list_sources() == []
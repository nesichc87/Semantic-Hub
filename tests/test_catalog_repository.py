from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine

from app.catalog.db import upgrade_database
from app.catalog.repository import CatalogConflictError, SourceCatalog


START = datetime(2026, 11, 26, 8, 0, tzinfo=timezone.utc)


class StepClock:
    """Returns START, START + 1 min, START + 2 min, ..."""

    def __init__(self):
        self.calls = 0

    def __call__(self) -> datetime:
        value = START + timedelta(minutes=self.calls)
        self.calls += 1
        return value


@pytest.fixture
def engine(catalog_url):
    upgrade_database(catalog_url)
    engine = create_engine(catalog_url)
    yield engine
    engine.dispose()


def make_catalog(engine, reserved_prefixes=()):
    return SourceCatalog(engine, reserved_prefixes=reserved_prefixes, clock=StepClock())


def rdf_entry(source_id="example", prefix="ex:"):
    return {
        "type": "rdf",
        "config": {
            "id": source_id,
            "prefix": prefix,
            "namespace": "https://example.org/vocab/",
            "locations": ["https://example.org/vocab.ttl"],
            "format": "turtle",
        },
    }


def test_add_stores_proposed_source_with_config_as_given(engine):
    catalog = make_catalog(engine)
    entry = rdf_entry()

    record = catalog.add(entry, license="CC BY 4.0")

    assert record.id == "example"
    assert record.type == "rdf"
    assert record.config == entry["config"]
    assert record.prefixes == ["ex:"]
    assert record.status == "proposed"
    assert record.status_reason is None
    assert record.license == "CC BY 4.0"
    assert record.created_at == START
    assert record.updated_at == START
    assert catalog.get("example") == record


def test_xsd_source_has_main_and_import_prefixes(engine):
    record = make_catalog(engine).add(
        {
            "type": "xsd",
            "config": {
                "id": "main",
                "prefix": "m:",
                "location": "https://example.org/main.xsd",
                "import_prefixes": {"urn:units": "u:"},
            },
        }
    )

    assert record.prefixes == ["m:", "u:"]


def test_sources_are_stored_and_listed_in_order(engine):
    make_catalog(engine).add(rdf_entry("first", "a:"))
    make_catalog(engine).add(rdf_entry("second", "b:"))

    assert [record.id for record in make_catalog(engine).list_sources()] == ["first", "second"]
    assert make_catalog(engine).get("missing") is None


def test_duplicate_source_id_is_conflict(engine):
    catalog = make_catalog(engine)
    catalog.add(rdf_entry("example", "a:"))

    with pytest.raises(CatalogConflictError):
        catalog.add(rdf_entry("example", "b:"))


@pytest.mark.parametrize("prefix", ["qudt:unit:", "qudt:", "qudt:unit:x:"])
def test_overlapping_prefix_is_conflict(engine, prefix):
    catalog = make_catalog(engine)
    catalog.add(rdf_entry("units", "qudt:unit:"))

    with pytest.raises(CatalogConflictError):
        catalog.add(rdf_entry("other", prefix))
    assert [record.id for record in catalog.list_sources()] == ["units"]


def test_non_overlapping_prefix_is_accepted(engine):
    catalog = make_catalog(engine)
    catalog.add(rdf_entry("units", "qudt:unit:"))

    catalog.add(rdf_entry("kinds", "qudt:quantitykind:"))

    assert len(catalog.list_sources()) == 2


@pytest.mark.parametrize("prefix", ["kbl:", "kb", "kbl:x:"])
def test_reserved_prefix_is_conflict(engine, prefix):
    catalog = make_catalog(engine, reserved_prefixes=["kbl:"])

    with pytest.raises(CatalogConflictError):
        catalog.add(rdf_entry("other", prefix))


@pytest.mark.parametrize(
    "entry",
    [
        {"type": "sparql", "config": rdf_entry()["config"]},
        {"type": "rdf", "config": {**rdf_entry()["config"], "prefix": ""}},
    ],
)
def test_invalid_entry_is_rejected_and_not_stored(engine, entry):
    catalog = make_catalog(engine)

    with pytest.raises(ValueError):
        catalog.add(entry)
    assert catalog.list_sources() == []


def test_set_status_updates_status_reason_and_time(engine):
    catalog = make_catalog(engine)
    catalog.add(rdf_entry())

    record = catalog.set_status("example", "rejected", reason="License unclear")

    assert record.status == "rejected"
    assert record.status_reason == "License unclear"
    assert record.updated_at == START + timedelta(minutes=1)
    assert catalog.get("example").status == "rejected"


@pytest.mark.parametrize("source_id, status", [("example", "unknown"), ("missing", "active")])
def test_set_status_rejects_unknown_status_or_source(engine, source_id, status):
    catalog = make_catalog(engine)
    catalog.add(rdf_entry())

    with pytest.raises(ValueError):
        catalog.set_status(source_id, status)
import json
import logging

import pytest

from app.catalog.repository import CatalogConflictError
from app.catalog.runtime import BUILTIN_PREFIXES, check_database, init_catalog


def sqlite_url(path) -> str:
    return f"sqlite:///{path.as_posix()}"


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


def write_seed(tmp_path):
    path = tmp_path / "seed.json"
    seed = [{"id": "units", "description": "Units", "license": "MIT", "entry": rdf_entry("units", "u:")}]
    path.write_text(json.dumps(seed), encoding="utf-8")
    return path


@pytest.fixture
def ok_state(catalog_url):
    state = init_catalog({"SEMANTIC_HUB_DATABASE_URL": catalog_url})
    yield state
    state.close()


def test_init_creates_catalog_on_reachable_database(ok_state):
    assert ok_state.error is None
    assert ok_state.catalog.list_sources() == []
    assert check_database(ok_state)


def test_init_reports_unreachable_database_instead_of_raising(tmp_path):
    state = init_catalog(
        {"SEMANTIC_HUB_DATABASE_URL": sqlite_url(tmp_path / "missing" / "catalog.db")}
    )
    try:
        assert state.catalog is None
        assert state.error
        assert not check_database(state)
    finally:
        state.close()


def test_builtin_prefixes_are_reserved(ok_state):
    assert set(BUILTIN_PREFIXES) == {"kbl:", "vec:", "qudt:unit:", "dppo:"}

    with pytest.raises(CatalogConflictError):
        ok_state.catalog.add(rdf_entry("other", "kbl:x:"))


def test_init_preselects_seed_sources(tmp_path, catalog_url):
    state = init_catalog(
        {
            "SEMANTIC_HUB_DATABASE_URL": catalog_url,
            "SEMANTIC_HUB_SEED_SOURCES": "units",
        },
        seed_path=write_seed(tmp_path),
    )
    try:
        assert [(record.id, record.status) for record in state.catalog.list_sources()] == [
            ("units", "approved")
        ]
    finally:
        state.close()


def test_failed_preselection_keeps_catalog_usable(tmp_path, catalog_url, caplog):
    with caplog.at_level(logging.WARNING):
        state = init_catalog(
            {
                "SEMANTIC_HUB_DATABASE_URL": catalog_url,
                "SEMANTIC_HUB_SEED_SOURCES": "missing",
            },
            seed_path=write_seed(tmp_path),
        )
    try:
        assert state.error is None
        assert state.catalog.list_sources() == []
        assert "missing" in caplog.text
    finally:
        state.close()
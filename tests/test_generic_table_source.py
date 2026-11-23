import logging

import pytest

import app.sources.generic.table as table_module
from app.sources.generic.config_schema import TableSourceConfig
from app.sources.generic.table import GenericTableSource


CSV = """Hinweis: Beispieltabelle, frei erfunden für den Test.
Nr;Code;Bezeichnung;Definition;Gleich wie
1;m;Meter;Basiseinheit der Länge;http://qudt.org/vocab/unit/M
2;kg;Kilogramm;Basiseinheit   der Masse;http://qudt.org/vocab/unit/KiloGM https://example.org/kg
3; s ;;;
4;m;Meter doppelt;;
5;"mm  Hg";"Millimeter
 Quecksilbersäule";;
;;;;
""".encode("utf-8")

LOCATION = "https://example.org/units.csv"


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
        "id": "t",
        "prefix": "t:",
        "location": LOCATION,
        "format": "csv",
        "header_row": 2,
        "columns": {
            "id": "Code",
            "name": "Bezeichnung",
            "description": "Definition",
            "equivalence": "Gleich wie",
        },
    }
    raw.update(overrides)
    return GenericTableSource(TableSourceConfig.model_validate(raw), fetch)


def test_resolves_row_with_normalized_name_and_description():
    concept = make_source(FakeFetch(CSV)).resolve("t:kg")

    assert concept.semantic_id == "t:kg"
    assert concept.source == "t"
    assert concept.name == "Kilogramm"
    assert concept.description == "Basiseinheit der Masse"
    assert concept.properties == []
    assert concept.data_type is None
    assert concept.provenance == {"source": "t", "source_reference": "t:kg"}


def test_identifier_is_only_stripped_and_used_as_fallback_name():
    source = make_source(FakeFetch(CSV))

    assert source.resolve("t:s").name == "s"
    assert source.resolve("t:s").description is None
    assert source.resolve("t:mm  Hg").name == "Millimeter Quecksilbersäule"
    with pytest.raises(ValueError):
        source.resolve("t:mm Hg")


def test_first_of_duplicate_identifiers_wins_and_is_logged(caplog):
    with caplog.at_level(logging.WARNING):
        concept = make_source(FakeFetch(CSV)).resolve("t:m")

    assert concept.name == "Meter"
    assert "'m'" in caplog.text


def test_equivalents_from_equivalence_column():
    assert make_source(FakeFetch(CSV)).equivalents() == {
        "t:m": {"http://qudt.org/vocab/unit/M"},
        "t:kg": {"http://qudt.org/vocab/unit/KiloGM", "https://example.org/kg"},
    }


def test_suggest_searches_name_and_identifier():
    fetch = FakeFetch(CSV)
    source = make_source(fetch)

    assert source.suggest("") == []
    assert fetch.calls == []
    assert source.suggest("kilo") == ["t:kg"]
    assert source.suggest("kg") == ["t:kg"]


def test_loads_once_and_failed_load_is_not_cached():
    fetch = FakeFetch(CSV, failures=1)
    source = make_source(fetch)

    with pytest.raises(RuntimeError):
        source.resolve("t:kg")
    source.resolve("t:kg")
    source.resolve("t:m")

    assert fetch.calls == [(LOCATION, "csv"), (LOCATION, "csv")]


@pytest.mark.parametrize(
    "data, overrides",
    [
        (CSV, {"columns": {"id": "Kennung"}}),
        (CSV, {"header_row": 20}),
        (b"Code\n\xff\xfe\n", {"header_row": 1, "columns": {"id": "Code"}}),
        (b"Code;Name\n;\n", {"header_row": 1, "columns": {"id": "Code"}}),
    ],
)
def test_unusable_table_raises_runtime_error(data, overrides):
    with pytest.raises(RuntimeError):
        make_source(FakeFetch(data), **overrides).resolve("t:m")


def test_too_many_rows_raise_runtime_error(monkeypatch):
    monkeypatch.setattr(table_module, "MAX_ROWS", 3)

    with pytest.raises(RuntimeError):
        make_source(FakeFetch(CSV)).resolve("t:m")
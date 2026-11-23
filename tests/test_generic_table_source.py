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

import io

from openpyxl import Workbook

LOCATION_XLSX = "https://example.org/units.xlsx"


def xlsx_bytes(sheets: dict[str, list[list]]) -> bytes:
    workbook = Workbook()
    workbook.remove(workbook.active)
    for title, rows in sheets.items():
        sheet = workbook.create_sheet(title)
        for row in rows:
            sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


UNITS_ROWS = [
    ["Copyright note, not a header"],
    ["Code", "Name", "Description"],
    ["mg/dL", "milligram per  deciliter", None],
    [2.0, "two", "Number used as code"],
    [None, None, None],
]

XLSX = xlsx_bytes({"Notes": [["Nothing here"]], "Units": UNITS_ROWS})


def make_xlsx_source(fetch, **overrides):
    raw = {
        "location": LOCATION_XLSX,
        "format": "xlsx",
        "sheet": "Units",
        "columns": {"id": "Code", "name": "Name", "description": "Description"},
    }
    raw.update(overrides)
    return make_source(fetch, **raw)


def test_xlsx_rows_from_configured_sheet():
    fetch = FakeFetch(XLSX)
    source = make_xlsx_source(fetch)

    assert source.resolve("t:mg/dL").name == "milligram per deciliter"
    assert source.resolve("t:mg/dL").description is None
    assert source.resolve("t:2").name == "two"
    assert fetch.calls == [(LOCATION_XLSX, "xlsx")]


def test_xlsx_without_sheet_uses_first_sheet():
    source = make_xlsx_source(FakeFetch(xlsx_bytes({"Units": UNITS_ROWS})), sheet=None)

    assert source.resolve("t:mg/dL").name == "milligram per deciliter"


def test_xlsx_unknown_sheet_raises_runtime_error():
    with pytest.raises(RuntimeError, match="Sheet 'Missing'"):
        make_xlsx_source(FakeFetch(XLSX), sheet="Missing").resolve("t:2")


def test_xlsx_that_is_not_a_zip_raises_runtime_error():
    with pytest.raises(RuntimeError, match="not a valid xlsx"):
        make_xlsx_source(FakeFetch(b"not a zip file")).resolve("t:2")


def test_xlsx_too_large_when_unpacked_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(table_module, "MAX_UNPACKED_BYTES", 100)

    with pytest.raises(RuntimeError, match="unpacked"):
        make_xlsx_source(FakeFetch(XLSX)).resolve("t:2")


def test_xlsx_too_many_rows_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(table_module, "MAX_ROWS", 2)

    with pytest.raises(RuntimeError, match="more than"):
        make_xlsx_source(FakeFetch(XLSX)).resolve("t:2")


def test_openpyxl_uses_defusedxml():
    from openpyxl.xml import DEFUSEDXML

    assert DEFUSEDXML is True
import pytest

from app.sources.generic.config_schema import XSDSourceConfig
from app.sources.generic.xsd import GenericXSDSource


MAIN = b"""<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:m="urn:main" targetNamespace="urn:main">
  <xs:complexType name="Base">
    <xs:annotation><xs:documentation>Base of  all
      things</xs:documentation></xs:annotation>
    <xs:sequence><xs:element name="Id" type="xs:ID"/></xs:sequence>
  </xs:complexType>
  <xs:complexType name="Wire">
    <xs:complexContent><xs:extension base="m:Base"><xs:sequence>
      <xs:element name="Length" type="m:LengthValue">
        <xs:annotation><xs:documentation>Length of the wire</xs:documentation></xs:annotation>
      </xs:element>
      <xs:element ref="m:Other"/>
    </xs:sequence></xs:extension></xs:complexContent>
  </xs:complexType>
  <xs:simpleType name="LengthValue"><xs:restriction base="m:Positive"/></xs:simpleType>
  <xs:simpleType name="Positive"><xs:restriction base="xs:double"/></xs:simpleType>
</xs:schema>"""

LOCATION = "https://example.org/main.xsd"


class FakeFetch:
    def __init__(self, files: dict[str, bytes], failures: int = 0):
        self.files = files
        self.failures = failures
        self.calls = []

    def __call__(self, location: str, fmt: str) -> bytes:
        self.calls.append((location, fmt))
        if self.failures:
            self.failures -= 1
            raise RuntimeError("source unavailable")
        if location not in self.files:
            raise RuntimeError(f"not found: {location}")
        return self.files[location]


def make_source(fetch, **overrides):
    raw = {"id": "main", "prefix": "m:", "location": LOCATION}
    raw.update(overrides)
    return GenericXSDSource(XSDSourceConfig.model_validate(raw), fetch)


def test_complex_type_with_inherited_properties_base_first():
    concept = make_source(FakeFetch({LOCATION: MAIN}), documentation=True).resolve("m:Wire")

    assert concept.semantic_id == "m:Wire"
    assert concept.source == "main"
    assert concept.name == "Wire"
    assert concept.description is None
    assert concept.data_type is None
    assert concept.provenance == {"source": "main", "source_reference": "m:Wire"}
    assert [
        (p.semantic_id, p.name, p.description, p.data_type) for p in concept.properties
    ] == [
        ("m:Wire:Id", "Id", None, "xs:ID"),
        ("m:Wire:Length", "Length", "Length of the wire", "m:LengthValue"),
    ]
    assert concept.properties[0].provenance == {"source": "main", "source_reference": "m:Wire"}


def test_documentation_only_when_configured():
    with_docs = make_source(FakeFetch({LOCATION: MAIN}), documentation=True)
    without_docs = make_source(FakeFetch({LOCATION: MAIN}))

    assert with_docs.resolve("m:Base").description == "Base of all things"
    assert without_docs.resolve("m:Base").description is None
    assert without_docs.resolve("m:Wire").properties[1].description is None


def test_simple_type_has_raw_restriction_base():
    concept = make_source(FakeFetch({LOCATION: MAIN})).resolve("m:LengthValue")

    assert concept.data_type == "m:Positive"
    assert concept.properties == []


def test_resolve_is_exact_and_can_resolve_checks_prefix():
    source = make_source(FakeFetch({LOCATION: MAIN}))

    with pytest.raises(ValueError):
        source.resolve("m:wire")
    assert source.can_resolve("m:Anything")
    assert not source.can_resolve("x:Wire")


def test_suggest_ranks_and_empty_query_does_not_load():
    fetch = FakeFetch({LOCATION: MAIN})
    source = make_source(fetch)

    assert source.suggest("") == []
    assert fetch.calls == []
    assert source.suggest("value") == ["m:LengthValue"]


def test_loads_once_with_xsd_format():
    fetch = FakeFetch({LOCATION: MAIN})
    source = make_source(fetch)

    source.resolve("m:Wire")
    source.resolve("m:Base")

    assert fetch.calls == [(LOCATION, "xsd")]


def test_failed_load_is_not_cached():
    fetch = FakeFetch({LOCATION: MAIN}, failures=1)
    source = make_source(fetch)

    with pytest.raises(RuntimeError):
        source.resolve("m:Wire")

    assert source.resolve("m:Wire").name == "Wire"


@pytest.mark.parametrize(
    "data",
    [
        b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "a">]><x>&a;</x>',
        b"<xs:schema",
    ],
)
def test_invalid_or_forbidden_xml_raises_runtime_error(data):
    with pytest.raises(RuntimeError):
        make_source(FakeFetch({LOCATION: data})).resolve("m:Wire")
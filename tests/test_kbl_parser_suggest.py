from app.sources.kbl.parser import KBLParser


XSD = b"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:complexType name="General_wire"/>
    <xs:complexType name="Wire"/>
    <xs:simpleType name="Wire_type">
        <xs:restriction base="xs:string"/>
    </xs:simpleType>
    <xs:complexType name="Connector"/>
</xs:schema>
"""


def test_suggest_types_ranks_exact_before_prefix_before_substring():
    parser = KBLParser()
    root = parser.parse(XSD)

    assert parser.suggest_types(root, "wire") == [
        "kbl:Wire",
        "kbl:Wire_type",
        "kbl:General_wire",
    ]


def test_suggest_types_returns_empty_list_for_blank_query():
    parser = KBLParser()
    root = parser.parse(XSD)

    assert parser.suggest_types(root, "   ") == []
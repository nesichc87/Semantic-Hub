from app.sources.kbl.client import KBLClient
from app.sources.kbl.parser import KBLParser
from app.sources.kbl.service import KBLService
from app.sources.kbl.parser import KBLParser, XS_NAMESPACE


KBL_XSD_URL = (
    "https://ecad-wiki.prostep.org/"
    "specifications/kbl/v25-sr1/kbl2.5-sr1.xsd"
)


def test_kbl_xsd_can_be_loaded():
    client = KBLClient(KBL_XSD_URL)

    content = client.get_xsd()

    assert content
    assert b"schema" in content


def test_kbl_xsd_can_be_parsed():
    client = KBLClient(KBL_XSD_URL)
    parser = KBLParser()

    content = client.get_xsd()
    root = parser.parse(content)

    assert root.tag.endswith("schema")

def test_inspect_kbl_container():
    client = KBLClient(KBL_XSD_URL)
    parser = KBLParser()

    content = client.get_xsd()
    root = parser.parse(content)

    container = parser.find_element(root, "KBL_container")

    assert container is not None

    type_name = parser.get_element_type(container)

    print(f"\nKBL_container type: {type_name}")

    assert type_name is not None

    complex_type = parser.get_complex_type(root, type_name)

    assert complex_type is not None

    print("Complex type found:")
    print(complex_type.get("name"))

    for child in complex_type.iter():
        if child.tag == f"{{{XS_NAMESPACE}}}element":
            print(
                "  element:",
                child.get("name"),
                "type:",
                child.get("type"),
            )
def test_component_inherits_part_elements():
    client = KBLClient(KBL_XSD_URL)
    parser = KBLParser()

    content = client.get_xsd()
    root = parser.parse(content)

    elements = parser.list_inherited_elements(
        root,
        "kbl:Component",
    )

    names = [
        element["name"]
        for element in elements
    ]

    print("\nResolved Component elements:")

    for name in names:
        print("  ", name)

    assert "Part_number" in names
    assert "Company_name" in names
    assert "Description" in names
    assert "Processing_information" in names



def test_resolve_multiple_kbl_types():
    client = KBLClient(KBL_XSD_URL)
    parser = KBLParser()

    content = client.get_xsd()
    root = parser.parse(content)

    type_names = [
        "kbl:Component",
        "kbl:Assembly_part",
        "kbl:Connector_housing",
    ]

    for type_name in type_names:
        elements = parser.list_inherited_elements(
            root,
            type_name,
        )

        print(f"\n=== {type_name} ===")
        print(f"Resolved elements: {len(elements)}")

        for element in elements[:10]:
            print(
                f"  {element['name']} "
                f"type={element['type']}"
                )

        assert elements

def test_resolve_multiple_kbl_types():
    client = KBLClient(KBL_XSD_URL)
    parser = KBLParser()

    content = client.get_xsd()
    root = parser.parse(content)

    type_names = [
        "kbl:Component",
        "kbl:Assembly_part",
        "kbl:Connector_housing",
    ]

    for type_name in type_names:
        elements = parser.list_inherited_elements(
            root,
            type_name,
        )

        print(f"\n=== {type_name} ===")
        print(f"Resolved elements: {len(elements)}")

        for element in elements[:10]:
            print(
                f"  {element['name']} "
                f"type={element['type']}"
            )

        assert elements

def test_kbl_service_resolves_component():
    client = KBLClient(KBL_XSD_URL)
    parser = KBLParser()

    service = KBLService(
        client=client,
        parser=parser,
    )

    result = service.get_type(
        "kbl:Component"
    )

    assert result["type"] == "kbl:Component"
    assert result["elements"]

    element_names = [
        element["name"]
        for element in result["elements"]
    ]

    assert "Part_number" in element_names
    assert "Company_name" in element_names
    assert "Description" in element_names
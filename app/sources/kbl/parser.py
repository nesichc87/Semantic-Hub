import xml.etree.ElementTree as ET


XS_NAMESPACE = "http://www.w3.org/2001/XMLSchema"

XS = {
    "xs": XS_NAMESPACE,
}


class KBLParser:
    """
    Parser for KBL XML Schema definitions.
    """

    def parse(self, xsd_content: bytes) -> ET.Element:
        """
        Parse raw XSD content into an XML tree.
        """

        try:
            return ET.fromstring(xsd_content)

        except ET.ParseError as exc:
            raise ValueError("Invalid KBL XSD document") from exc

    def list_elements(self, root: ET.Element) -> list[str]:
        """
        Return the names of all global XSD elements.
        """

        elements = root.findall("xs:element", XS)

        return [
            element.get("name")
            for element in elements
            if element.get("name")
        ]

    def find_element(
        self,
        root: ET.Element,
        name: str,
    ) -> ET.Element | None:
        """
        Find a global XSD element by name.
        """

        for element in root.findall("xs:element", XS):
            if element.get("name") == name:
                return element

        return None

    def list_child_elements(
        self,
        element: ET.Element,
    ) -> list[str]:
        """
        Return the names of direct child XSD elements.
        """

        result = []

        for child in element.iter():
            if child.tag == f"{{{XS_NAMESPACE}}}element":
                name = child.get("name")

                if name:
                    result.append(name)

        return result

    def get_complex_type(
            self,
            root: ET.Element,
            type_name: str,
    ) -> ET.Element | None:
        """
        Find a named XSD complexType.

        XSD type references may contain a namespace prefix,
        for example ``kbl:KBL_container``.
        """

        local_name = type_name.split(":", 1)[-1]

        for complex_type in root.findall("xs:complexType", XS):
            if complex_type.get("name") == local_name:
                return complex_type

        return None

    def get_element_type(
        self,
        element: ET.Element,
    ) -> str | None:
        """
        Return the referenced XSD type of an element.
        """

        return element.get("type")

    def list_type_elements(
            self,
            complex_type: ET.Element,
    ) -> list[dict[str, str | None]]:
        """
        Return the XSD elements defined directly inside a complex type.
        Supports direct sequences and complexContent/extension structures.
        """

        result = []

        for element in complex_type.iter(
                f"{{{XS_NAMESPACE}}}element"
        ):
            result.append(
                {
                    "name": element.get("name"),
                    "type": element.get("type"),
                    "min_occurs": element.get("minOccurs"),
                    "max_occurs": element.get("maxOccurs"),
                }
            )

        return result

    def resolve_complex_type(
            self,
            root: ET.Element,
            type_name: str,
    ) -> list[ET.Element]:
        """
        Resolve a complex type including inherited types.

        Returns the complex types from the base type up to the
        requested type.
        """

        result = []

        current_type = type_name
        visited = set()

        while current_type:
            local_name = current_type.split(":", 1)[-1]

            if local_name in visited:
                raise ValueError(
                    f"Circular XSD inheritance detected at '{local_name}'"
                )

            visited.add(local_name)

            complex_type = self.get_complex_type(
                root,
                current_type,
            )

            if complex_type is None:
                break

            result.append(complex_type)

            current_type = self.get_base_type(
                complex_type
            )

        return result

    def list_inherited_elements(
            self,
            root: ET.Element,
            type_name: str,
    ) -> list[dict[str, str | None]]:
        """
        Return all XSD elements of a complex type including
        elements inherited from base types.
        """

        types = self.resolve_complex_type(
            root,
            type_name,
        )

        result = []

        # Base type first, derived type last.
        for complex_type in reversed(types):
            result.extend(
                self.list_type_elements(complex_type)
            )

        return result

    def get_base_type(
            self,
            complex_type: ET.Element,
    ) -> str | None:
        """
        Return the base type of a complexContent extension.
        """

        complex_content = complex_type.find(
            "xs:complexContent",
            XS,
        )

        if complex_content is None:
            return None

        extension = complex_content.find(
            "xs:extension",
            XS,
        )

        if extension is None:
            return None

        return extension.get("base")
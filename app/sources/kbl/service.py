from app.sources.kbl.client import KBLClient
from app.sources.kbl.parser import KBLParser


class KBLService:
    """
    High-level service for resolving KBL types and their elements.
    """

    def __init__(
        self,
        client: KBLClient,
        parser: KBLParser,
    ):
        self.client = client
        self.parser = parser

    def get_type(
        self,
        type_name: str,
    ) -> dict:
        """
        Resolve a KBL complex type and return its elements.
        """

        content = self.client.get_xsd()
        root = self.parser.parse(content)

        elements = self.parser.list_inherited_elements(
            root,
            type_name,
        )

        if not elements:
            raise ValueError(
                f"KBL type '{type_name}' not found"
            )

        return {
            "type": type_name,
            "elements": elements,
        }
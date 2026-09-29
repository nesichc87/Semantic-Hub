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
        self._root = None

    def _get_root(self):
        """
        Return the parsed KBL XSD.

        The XSD is loaded and parsed on first use and then kept in
        memory. The KBL XSD is a fixed release, so no invalidation
        is required.
        """

        if self._root is None:
            content = self.client.get_xsd()
            self._root = self.parser.parse(content)

        return self._root

    def get_type(
        self,
        type_name: str,
    ) -> dict:
        """
        Resolve a KBL type and return its semantic information.
        """

        root = self._get_root()

        type_kind = self.parser.resolve_type(
            root,
            type_name,
        )

        if type_kind == "unknown":
            raise ValueError(
                f"KBL type '{type_name}' not found"
            )

        if type_kind == "builtin":
            return {
                "type": type_name,
                "kind": "builtin",
            }

        if type_kind == "simple":
            simple_type = self.parser.get_simple_type(
                root,
                type_name,
            )

            return {
                "type": type_name,
                "kind": "simple",
                "base_type": self.parser.get_simple_type_base(
                    simple_type
                ),
            }

        if type_kind == "complex":
            elements = self.parser.list_inherited_elements(
                root,
                type_name,
            )

            return {
                "type": type_name,
                "kind": "complex",
                "elements": elements,
            }

        raise ValueError(
            f"Unsupported KBL type '{type_name}'"
        )

    def suggest_types(self, query: str) -> list[str]:
        """
        Suggest KBL type identifiers matching the query.

        Matching is case-insensitive. Resolution itself remains
        case-sensitive and exact.
        """

        root = self._get_root()

        return self.parser.suggest_types(
            root,
            query,
        )
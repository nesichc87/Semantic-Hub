from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS

from app.sources.qudt.client import QUDTClient


QUDT_SCHEMA_NAMESPACE = "http://qudt.org/schema/qudt/"
QUDT_UNIT_NAMESPACE = "http://qudt.org/vocab/unit/"
UNIT_PREFIX = "qudt:unit:"

QUDT_UNIT = URIRef(QUDT_SCHEMA_NAMESPACE + "Unit")
QUDT_PLAIN_TEXT_DESCRIPTION = URIRef(
    QUDT_SCHEMA_NAMESPACE + "plainTextDescription"
)


class QUDTService:
    """
    High-level service for resolving QUDT units.
    """

    def __init__(self, client: QUDTClient):
        self.client = client
        self._graph = None

    def _get_graph(self) -> Graph:
        """
        Return the parsed QUDT unit vocabulary.

        The vocabulary is loaded and parsed on first use and then kept
        in memory for the lifetime of the process. QUDT publishes new
        releases regularly, so a restart picks up the current release.
        """

        if self._graph is None:
            graph = Graph()
            graph.parse(data=self.client.get_ttl(), format="turtle")
            self._graph = graph

        return self._graph

    def get_unit(self, semantic_id: str) -> dict:
        """
        Resolve a QUDT unit by its exact, case-sensitive identifier.
        """

        graph = self._get_graph()
        local_name = self._local_name(semantic_id)
        unit = URIRef(QUDT_UNIT_NAMESPACE + local_name)

        if (unit, RDF.type, QUDT_UNIT) not in graph:
            raise ValueError(f"QUDT unit '{semantic_id}' not found")

        description = self._english_literal(
            graph, unit, QUDT_PLAIN_TEXT_DESCRIPTION
        ) or self._english_literal(graph, unit, DCTERMS.description)

        return {
            "name": self._english_literal(graph, unit, RDFS.label) or local_name,
            "description": description,
        }

    def suggest_units(self, query: str) -> list[str]:
        """
        Suggest QUDT unit identifiers matching the query.

        Matches the local name and English or untagged labels,
        case-insensitively. Resolution itself remains case-sensitive
        and exact.
        """

        search = query.strip().lower()

        if not search:
            return []

        graph = self._get_graph()
        matches = set()

        for unit in graph.subjects(RDF.type, QUDT_UNIT):
            if not isinstance(unit, URIRef) or not str(unit).startswith(
                QUDT_UNIT_NAMESPACE
            ):
                continue

            local_name = str(unit)[len(QUDT_UNIT_NAMESPACE):]
            labels = (
                str(o)
                for o in graph.objects(unit, RDFS.label)
                if isinstance(o, Literal) and o.language in (None, "en")
            )

            if search in local_name.lower() or any(
                search in label.lower() for label in labels
            ):
                matches.add(UNIT_PREFIX + local_name)

        return sorted(matches)

    @staticmethod
    def _local_name(semantic_id: str) -> str:
        if not semantic_id.startswith(UNIT_PREFIX):
            raise ValueError(f"Not a QUDT unit identifier: '{semantic_id}'")

        return semantic_id[len(UNIT_PREFIX):]

    @staticmethod
    def _english_literal(
        graph: Graph, node: URIRef, predicate: URIRef
    ) -> str | None:
        """
        Return the first English or untagged literal (sorted), or None.

        Only the exact language tag 'en' counts as English. Regional
        variants such as 'en-US' are ignored.
        """

        values = sorted(
            str(o).strip()
            for o in graph.objects(node, predicate)
            if isinstance(o, Literal) and o.language in (None, "en")
        )

        return values[0] if values else None
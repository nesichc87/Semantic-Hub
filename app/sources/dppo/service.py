from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from app.sources.dppo.client import DPPOClient
from app.sources.ranking import rank_matches


DPPO_NAMESPACE = "http://w3id.org/dppo/ontology/"
XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema#"

DPPO_MODULES = ("dpp-odp", "dpp-core", "dpp-info", "dpp-comp", "dpp-prov")


class DPPOService:
    """
    High-level service for resolving DPPO classes and their properties.

    Semantic identifiers follow the scheme 'dppo:<module>:<LocalName>',
    e.g. 'dppo:dpp-core:ComponentDPP'. IRIs that do not fit this scheme
    (such as IRIs containing a version segment) are not resolvable.
    """

    def __init__(self, client: DPPOClient):
        self.client = client
        self._graph = None

    def _get_graph(self) -> Graph:
        """
        Return all DPPO modules parsed into a single graph.

        The modules are loaded and parsed on first use and then kept in
        memory. A failed load is not cached.
        """

        if self._graph is None:
            graph = Graph()

            for module in DPPO_MODULES:
                graph.parse(data=self.client.get_ttl(module), format="turtle")

            self._graph = graph

        return self._graph

    def get_class(self, semantic_id: str) -> dict:
        """
        Resolve a DPPO class and return its direct and inherited
        properties. Inherited properties come first, starting with the
        most general base class.

        Properties whose domain is a blank node (e.g. owl:unionOf) are
        not included.
        """

        module, name = self._parse_id(semantic_id)
        graph = self._get_graph()
        cls = URIRef(f"{DPPO_NAMESPACE}{module}/{name}")

        if (cls, RDF.type, OWL.Class) not in graph:
            raise ValueError(f"DPPO class '{semantic_id}' not found")

        properties = []
        seen = set()

        for current in self._class_hierarchy(graph, cls):
            for prop in sorted(graph.subjects(RDFS.domain, current), key=str):
                if prop in seen:
                    continue

                seen.add(prop)
                properties.append(self._describe_property(graph, prop))

        return {
            "name": name,
            "description": self._comment(graph, cls),
            "properties": properties,
        }

    def suggest_classes(self, query: str) -> list[str]:
        """
        Suggest DPPO class identifiers matching the query.

        Matching is case-insensitive on the local class name. Results are
        ranked: exact matches first, then prefix matches, then substring
        matches. Resolution itself remains case-sensitive and exact.
        """

        if not query.strip():
            return []

        graph = self._get_graph()
        candidates = {}

        for cls in graph.subjects(RDF.type, OWL.Class):
            if not isinstance(cls, URIRef):
                continue

            semantic_id = self._compact(str(cls))

            if semantic_id.startswith("dppo:"):
                candidates[semantic_id] = [semantic_id.rsplit(":", 1)[1]]

        return rank_matches(query, candidates)

    @staticmethod
    def _class_hierarchy(graph: Graph, cls: URIRef) -> list[URIRef]:
        """
        Return the class and all of its superclasses, base classes first.

        Only named classes are followed. Blank nodes are ignored.
        """

        ordered = []
        visited = set()

        def visit(current: URIRef) -> None:
            if current in visited:
                return

            visited.add(current)

            superclasses = sorted(
                (
                    s for s in graph.objects(current, RDFS.subClassOf)
                    if isinstance(s, URIRef)
                ),
                key=str,
            )

            for superclass in superclasses:
                visit(superclass)

            ordered.append(current)

        visit(cls)

        return ordered

    def _describe_property(self, graph: Graph, prop: URIRef) -> dict:
        ranges = sorted(str(r) for r in graph.objects(prop, RDFS.range))

        return {
            "semantic_id": self._compact(str(prop)),
            "name": str(prop).rsplit("/", 1)[-1],
            "description": self._comment(graph, prop),
            "data_type": self._compact(ranges[0]) if ranges else None,
        }

    @staticmethod
    def _parse_id(semantic_id: str) -> tuple[str, str]:
        parts = semantic_id.split(":", 2)

        if len(parts) != 3 or parts[0] != "dppo":
            raise ValueError(f"Not a DPPO identifier: '{semantic_id}'")

        _, module, name = parts

        if module not in DPPO_MODULES or not name or "/" in name:
            raise ValueError(f"Not a DPPO identifier: '{semantic_id}'")

        return module, name

    @staticmethod
    def _compact(uri: str) -> str:
        if uri.startswith(DPPO_NAMESPACE):
            module, _, name = uri[len(DPPO_NAMESPACE):].partition("/")

            if module in DPPO_MODULES and name and "/" not in name:
                return f"dppo:{module}:{name}"

        if uri.startswith(XSD_NAMESPACE):
            return "xs:" + uri[len(XSD_NAMESPACE):]

        return uri

    @staticmethod
    def _comment(graph: Graph, node: URIRef) -> str | None:
        comments = [
            c for c in graph.objects(node, RDFS.comment)
            if isinstance(c, Literal)
        ]
        preferred = [
            c for c in comments if c.language in (None, "en")
        ] or comments

        if not preferred:
            return None

        return sorted(str(c) for c in preferred)[0].strip()
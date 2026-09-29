from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from app.sources.vec.client import VECClient


VEC_NAMESPACE = "http://www.prostep.org/ontologies/ecad/2024/03/vec#"
XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema#"


class VECService:
    """
    High-level service for resolving VEC ontology classes and their
    properties.
    """

    def __init__(self, client: VECClient):
        self.client = client
        self._graph = None

    def _get_graph(self) -> Graph:
        """
        Return the parsed VEC ontology.

        The ontology is loaded and parsed on first use and then kept in
        memory. The VEC ontology is a fixed release, so no invalidation
        is required.
        """

        if self._graph is None:
            graph = Graph()
            graph.parse(data=self.client.get_ttl(), format="turtle")
            self._graph = graph

        return self._graph

    def get_class(self, semantic_id: str) -> dict:
        """
        Resolve a VEC class and return its direct properties.
        """

        graph = self._get_graph()
        name = self._local_name(semantic_id)
        cls = URIRef(VEC_NAMESPACE + name)

        if (cls, RDF.type, OWL.Class) not in graph:
            raise ValueError(f"VEC class '{semantic_id}' not found")

        properties = [
            self._describe_property(graph, prop)
            for prop in graph.subjects(RDFS.domain, cls)
        ]
        properties.sort(key=lambda p: p["semantic_id"])

        return {
            "name": name,
            "description": self._comment(graph, cls),
            "properties": properties,
        }

    def _describe_property(self, graph: Graph, prop: URIRef) -> dict:
        ranges = sorted(str(r) for r in graph.objects(prop, RDFS.range))

        return {
            "semantic_id": self._compact(str(prop)),
            "name": str(prop).split("#")[-1],
            "description": self._comment(graph, prop),
            "data_type": self._compact(ranges[0]) if ranges else None,
        }

    @staticmethod
    def _local_name(semantic_id: str) -> str:
        if not semantic_id.startswith("vec:"):
            raise ValueError(f"Not a VEC identifier: '{semantic_id}'")

        return semantic_id.split(":", 1)[1]

    @staticmethod
    def _compact(uri: str) -> str:
        if uri.startswith(VEC_NAMESPACE):
            return "vec:" + uri[len(VEC_NAMESPACE):]

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
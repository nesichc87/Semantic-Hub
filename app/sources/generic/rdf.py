"""Generic RDF source type: a source defined by configuration only.

Data is read through an injected fetch function, so that the source
does not access files or URLs itself. Predicates from the configuration
are evaluated as single predicates, never as SPARQL.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from rdflib import RDF, Graph, Literal, URIRef

from app.models.semantic import SemanticConcept
from app.sources.base import SemanticSource
from app.sources.generic.config_schema import RDFSourceConfig
from app.sources.ranking import rank_matches


Fetch = Callable[[str, str], bytes]
"""Returns the raw data for a location; arguments are location and format."""


@dataclass
class _Entry:
    labels: list[tuple[str, str | None]] = field(default_factory=list)
    descriptions: list[tuple[str, str | None]] = field(default_factory=list)


class GenericRDFSource(SemanticSource):

    def __init__(self, config: RDFSourceConfig, fetch: Fetch):
        self.config = config
        self._fetch = fetch
        self._graph: Graph | None = None
        self._entries: dict[str, _Entry] | None = None

    # ---------- SemanticSource ----------

    def can_resolve(self, semantic_id: str) -> bool:
        return semantic_id.startswith(self.config.prefix)

    def resolve(self, semantic_id: str) -> SemanticConcept:
        if not self.can_resolve(semantic_id):
            raise ValueError(f"Unknown semantic ID: {semantic_id}")

        iri = self._to_iri(semantic_id)
        entry = self._get_entries().get(iri)
        if entry is None:
            raise ValueError(f"Unknown semantic ID: {semantic_id}")

        return SemanticConcept(
            semantic_id=semantic_id,
            source=self.config.id,
            name=self._name(iri, entry),
            description=self._pick(entry.descriptions),
            properties=[],
            provenance={
                "source": self.config.id,
                "source_reference": semantic_id,
            },
        )

    def suggest(self, query: str) -> list[str]:
        if not query.strip():
            return []

        use_labels = self.config.name_from != "local_name"
        candidates = {
            self._to_semantic_id(iri): [
                self._short_name(iri),
                *(
                    text
                    for text, lang in entry.labels
                    if use_labels and lang in self.config.languages
                ),
            ]
            for iri, entry in self._get_entries().items()
        }
        return rank_matches(query, candidates)

    # ---------- Loading ----------

    def _get_entries(self) -> dict[str, _Entry]:
        if self._entries is None:
            graph = Graph()
            for location in self.config.locations:
                data = self._fetch(location, self.config.format)
                graph.parse(data=data, format=self.config.format)
            # Assigned only after a successful load, so errors are not cached.
            self._entries = self._index(graph)
            self._graph = graph
        return self._entries

    def _index(self, graph: Graph) -> dict[str, _Entry]:
        entries: dict[str, _Entry] = {}

        allowed: set[str] | None = None
        if self.config.types:
            allowed = set()
            for type_name in self.config.types:
                type_iri = URIRef(self.config.expand(type_name))
                for subject in graph.subjects(RDF.type, type_iri):
                    if self._in_namespace(subject):
                        allowed.add(str(subject))

        if self.config.name_from != "label" and allowed is not None:
            for key in allowed:
                entries.setdefault(key, _Entry())

        for predicate in self.config.label:
            for subject, value in graph.subject_objects(URIRef(self.config.expand(predicate))):
                key = str(subject)
                if not self._in_namespace(subject) or not isinstance(value, Literal):
                    continue
                if allowed is not None and key not in allowed:
                    continue
                entries.setdefault(key, _Entry()).labels.append(
                    (self._text(value), value.language)
                )

        # Description predicates in order of priority: a later predicate only
        # fills entries for which an earlier one found nothing suitable.
        for predicate in self.config.description:
            found: dict[str, list[tuple[str, str | None]]] = {}
            for subject, value in graph.subject_objects(URIRef(self.config.expand(predicate))):
                key = str(subject)
                if key in entries and isinstance(value, Literal):
                    found.setdefault(key, []).append((self._text(value), value.language))
            for key, values in found.items():
                if self._pick(entries[key].descriptions) is None:
                    entries[key].descriptions.extend(values)

        return entries

    # ---------- Identifiers ----------

    def _to_iri(self, semantic_id: str) -> str:
        local = semantic_id[len(self.config.prefix):]
        for original, replacement in self.config.id_separators.items():
            local = local.replace(replacement, original)
        return self.config.namespace + local

    def _to_semantic_id(self, iri: str) -> str:
        local = iri[len(self.config.namespace):]
        for original, replacement in self.config.id_separators.items():
            local = local.replace(original, replacement)
        return self.config.prefix + local

    def _short_name(self, iri: str) -> str:
        """Last segment of the IRI after the namespace, e.g. "ComponentDPP"."""
        local = iri[len(self.config.namespace):]
        return local.rsplit("#", 1)[-1].rsplit("/", 1)[-1]

    def _in_namespace(self, subject) -> bool:
        iri = str(subject)
        return (
            isinstance(subject, URIRef)
            and iri.startswith(self.config.namespace)
            and iri != self.config.namespace
        )

    # ---------- Helpers ----------

    def _text(self, literal: Literal) -> str:
        if self.config.whitespace == "strip":
            return str(literal).strip()
        return " ".join(str(literal).split())

    def _pick(self, values: list[tuple[str, str | None]]) -> str | None:
        values = [(text, lang) for text, lang in values if text]
        for language in self.config.languages:
            matches = sorted(text for text, lang in values if lang == language)
            if matches:
                return matches[0]
        return None

    def _name(self, iri: str, entry: _Entry) -> str:
        if self.config.name_from == "local_name":
            return self._short_name(iri)
        return self._pick(entry.labels) or self._short_name(iri)
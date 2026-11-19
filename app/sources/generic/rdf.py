"""Generic RDF source type: a source defined by configuration only.

Data is read through an injected fetch function, so that the source
does not access files or URLs itself. Predicates from the configuration
are evaluated as single predicates, never as SPARQL.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from rdflib import RDF, Graph, Literal, URIRef

from app.models.semantic import SemanticConcept, SemanticProperty
from app.sources.base import SemanticSource
from app.sources.generic.config_schema import RDFSourceConfig
from app.sources.ranking import rank_matches


Fetch = Callable[[str, str], bytes]
"""Returns the raw data for a location; arguments are location and format."""


@dataclass
class _Entry:
    labels: list[tuple[str, str | None]] = field(default_factory=list)
    descriptions: list[tuple[str, str | None]] = field(default_factory=list)
    equivalents: set[str] = field(default_factory=set)


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
            properties=self._properties(URIRef(iri)) if self.config.properties else [],
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

    def equivalents(self) -> dict[str, set[str]]:
        """Equivalences per semantic ID.

        Targets from ``equivalence`` are full IRIs, targets from
        ``code_links`` are semantic IDs of another source.
        """
        return {
            self._to_semantic_id(iri): set(entry.equivalents)
            for iri, entry in self._get_entries().items()
            if entry.equivalents
        }

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

        # Equivalences are read in both directions; targets are kept as full IRIs.
        for predicate in self.config.equivalence:
            predicate_iri = URIRef(self.config.expand(predicate))
            for subject, target in graph.subject_objects(predicate_iri):
                for own, other in ((subject, target), (target, subject)):
                    entry = entries.get(str(own))
                    if entry is not None and isinstance(other, URIRef):
                        entry.equivalents.add(str(other))

        # Literal codes become semantic IDs of another source, e.g. "m" -> "ucum:m".
        for predicate, target_prefix in self.config.code_links.items():
            predicate_iri = URIRef(self.config.expand(predicate))
            for subject, value in graph.subject_objects(predicate_iri):
                entry = entries.get(str(subject))
                code = str(value).strip()
                if entry is not None and isinstance(value, Literal) and code:
                    entry.equivalents.add(target_prefix + code)

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

    def _compact(self, iri: str) -> str:
        """Semantic ID for IRIs of this source, else a configured short form, else the IRI."""
        if iri.startswith(self.config.namespace) and iri != self.config.namespace:
            return self._to_semantic_id(iri)
        for namespace, prefix in self.config.compact.items():
            if iri.startswith(namespace):
                return prefix + iri[len(namespace):]
        return iri

    def _in_namespace(self, subject) -> bool:
        iri = str(subject)
        return (
            isinstance(subject, URIRef)
            and iri.startswith(self.config.namespace)
            and iri != self.config.namespace
        )

    # ---------- Properties via domain and inheritance ----------

    def _properties(self, cls: URIRef) -> list[SemanticProperty]:
        cfg = self.config.properties
        graph = self._graph
        domain = URIRef(self.config.expand(cfg.domain))
        superclass = URIRef(self.config.expand(cfg.superclass))
        range_predicate = URIRef(self.config.expand(cfg.range))
        comment = URIRef(self.config.expand(cfg.description))

        # Most general class first; blank nodes (e.g. owl:Restriction) are ignored.
        ordered: list[URIRef] = []
        visited: set[URIRef] = set()

        def visit(current: URIRef) -> None:
            if current in visited:
                return
            visited.add(current)
            parents = sorted(
                (p for p in graph.objects(current, superclass) if isinstance(p, URIRef)),
                key=str,
            )
            for parent in parents:
                visit(parent)
            ordered.append(current)

        visit(cls)

        result: list[SemanticProperty] = []
        seen: set[URIRef] = set()
        for current in ordered:
            for prop in sorted(graph.subjects(domain, current), key=str):
                if prop in seen or not isinstance(prop, URIRef):
                    continue
                seen.add(prop)
                ranges = sorted(
                    str(r) for r in graph.objects(prop, range_predicate) if isinstance(r, URIRef)
                )
                comments = [
                    (self._text(c), c.language)
                    for c in graph.objects(prop, comment)
                    if isinstance(c, Literal)
                ]
                semantic_id = self._compact(str(prop))
                result.append(
                    SemanticProperty(
                        semantic_id=semantic_id,
                        name=_last_segment(str(prop)),
                        description=self._pick(comments),
                        data_type=self._compact(ranges[0]) if ranges else None,
                        unit=None,
                        provenance={
                            "source": self.config.id,
                            "source_reference": semantic_id,
                        },
                    )
                )
        return result

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

def _last_segment(iri: str) -> str:
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
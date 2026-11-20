"""Generic XSD source type: a source defined by configuration only.

Concepts are the named global complex and simple types of an XML Schema.
XML is parsed with defusedxml; DTDs are forbidden. Type names are kept as
written in the schema (e.g. "xs:string"); a simple type reports the base
of its restriction, one level only.
"""

import io
import logging
from dataclasses import dataclass
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, ParseError

from defusedxml import ElementTree as SafeET
from defusedxml.common import DefusedXmlException

from app.models.semantic import SemanticConcept, SemanticProperty
from app.sources.base import SemanticSource
from app.sources.generic.config_schema import XSDSourceConfig
from app.sources.generic.rdf import Fetch
from app.sources.ranking import rank_matches


XS_NAMESPACE = "http://www.w3.org/2001/XMLSchema"
logger = logging.getLogger(__name__)

def _q(tag: str) -> str:
    return f"{{{XS_NAMESPACE}}}{tag}"


@dataclass
class _XsdType:
    name: str
    kind: str  # "complexType" or "simpleType"
    namespace: str | None
    node: Element
    nsmap: dict[str, str]


class GenericXSDSource(SemanticSource):

    def __init__(self, config: XSDSourceConfig, fetch: Fetch):
        self.config = config
        self._fetch = fetch
        self._types: dict[tuple[str | None, str], _XsdType] | None = None
        self._prefixes: dict[str | None, str] = {}

    # ---------- SemanticSource ----------

    def can_resolve(self, semantic_id: str) -> bool:
        return any(semantic_id.startswith(prefix) for prefix in self._configured_prefixes())

    def resolve(self, semantic_id: str) -> SemanticConcept:
        if not self.can_resolve(semantic_id):
            raise ValueError(f"Unknown semantic ID: {semantic_id}")

        types = self._get_types()
        xsd_type = types.get(self._to_key(semantic_id))
        if xsd_type is None:
            raise ValueError(f"Unknown semantic ID: {semantic_id}")

        if xsd_type.kind == "simpleType":
            restriction = xsd_type.node.find(_q("restriction"))
            data_type = restriction.get("base") if restriction is not None else None
            properties = []
        else:
            data_type = None
            properties = self._properties(xsd_type, semantic_id)

        return SemanticConcept(
            semantic_id=semantic_id,
            source=self.config.id,
            name=xsd_type.name,
            description=self._documentation(xsd_type.node),
            properties=properties,
            provenance={"source": self.config.id, "source_reference": semantic_id},
            data_type=data_type,
        )

    def suggest(self, query: str) -> list[str]:
        if not query.strip():
            return []

        candidates = {}
        for xsd_type in self._get_types().values():
            semantic_id = self._to_semantic_id(xsd_type)
            if semantic_id is not None:
                candidates[semantic_id] = [xsd_type.name]
        return rank_matches(query, candidates)

    # ---------- Loading ----------

    def _get_types(self) -> dict[tuple[str | None, str], _XsdType]:
        if self._types is None:
            types: dict[tuple[str | None, str], _XsdType] = {}
            target_namespace = self._load_schema(self.config.location, types, set())
            # Assigned only after a successful load, so errors are not cached.
            self._prefixes = {target_namespace: self.config.prefix, **self.config.import_prefixes}
            self._types = types
        return self._types

    def _load_schema(self, location: str, types: dict, seen: set[str]) -> str | None:
        """Parse one schema, collect its named types, return its target namespace.

        With ``follow``, included and imported schemas are loaded as well.
        Each location is loaded once. A failing include or import is skipped
        and logged; only a failure of the main schema is raised.
        """
        seen.add(location)
        raw = self._fetch(location, "xsd")
        nsmap: dict[str, str] = {}
        root: Element | None = None
        try:
            for event, item in SafeET.iterparse(
                    io.BytesIO(raw), events=("start-ns", "start"), forbid_dtd=True
            ):
                if event == "start-ns":
                    prefix, uri = item
                    nsmap.setdefault(prefix, uri)
                elif root is None:
                    root = item
        except (ParseError, DefusedXmlException) as exc:
            raise RuntimeError(f"Invalid or forbidden XSD document: {location}") from exc

        target_namespace = root.get("targetNamespace")
        for kind in self.config.kinds:
            for node in root.findall(_q(kind)):
                name = node.get("name")
                if name:
                    types[(target_namespace, name)] = _XsdType(
                        name=name,
                        kind=kind,
                        namespace=target_namespace,
                        node=node,
                        nsmap=nsmap,
                    )

        if self.config.follow:
            for tag in ("include", "import"):
                for reference in root.findall(_q(tag)):
                    schema_location = reference.get("schemaLocation")
                    if not schema_location:
                        logger.warning(
                            "Skipped %s of namespace %s without schemaLocation in %s",
                            tag, reference.get("namespace"), location,
                        )
                        continue
                    referenced = urljoin(location, schema_location)
                    if referenced in seen:
                        continue
                    try:
                        self._load_schema(referenced, types, seen)
                    except RuntimeError:
                        logger.warning(
                            "Skipped %s %s referenced in %s",
                            tag, referenced, location, exc_info=True,
                        )

        return target_namespace

    # ---------- Properties ----------

    def _properties(self, xsd_type: _XsdType, semantic_id: str) -> list[SemanticProperty]:
        result = []
        for current in self._hierarchy(xsd_type):
            for element in current.node.iter(_q("element")):
                name = element.get("name")
                if not name:
                    continue  # e.g. <xs:element ref="..."/>
                result.append(
                    SemanticProperty(
                        semantic_id=f"{semantic_id}:{name}",
                        name=name,
                        description=self._documentation(element),
                        data_type=element.get("type"),
                        unit=None,
                        provenance={"source": self.config.id, "source_reference": semantic_id},
                    )
                )
        return result

    def _hierarchy(self, xsd_type: _XsdType) -> list[_XsdType]:
        """Base type first, derived type last (complexContent/extension)."""
        chain: list[_XsdType] = []
        visited: set[tuple[str | None, str]] = set()
        current: _XsdType | None = xsd_type
        while current is not None:
            key = (current.namespace, current.name)
            if key in visited:
                raise ValueError(f"Circular XSD inheritance at '{current.name}'")
            visited.add(key)
            chain.append(current)
            extension = current.node.find(f"{_q('complexContent')}/{_q('extension')}")
            base = self._qname(extension.get("base"), current.nsmap) if extension is not None else None
            current = self._types.get(base) if base else None
            if current is not None and current.kind != "complexType":
                current = None
        return list(reversed(chain))

    # ---------- Identifiers ----------

    def _configured_prefixes(self) -> list[str]:
        return [self.config.prefix, *self.config.import_prefixes.values()]

    def _to_key(self, semantic_id: str) -> tuple[str | None, str] | None:
        # Longest prefix first, so that nested prefixes are matched correctly.
        for namespace, prefix in sorted(self._prefixes.items(), key=lambda item: -len(item[1])):
            if semantic_id.startswith(prefix):
                return namespace, semantic_id[len(prefix):]
        return None

    def _to_semantic_id(self, xsd_type: _XsdType) -> str | None:
        prefix = self._prefixes.get(xsd_type.namespace)
        return prefix + xsd_type.name if prefix else None

    @staticmethod
    def _qname(value: str, nsmap: dict[str, str]) -> tuple[str | None, str]:
        prefix, _, local = value.rpartition(":")
        return (nsmap.get(prefix) if prefix else nsmap.get("")), local

    # ---------- Helpers ----------

    def _documentation(self, node: Element) -> str | None:
        if not self.config.documentation:
            return None
        doc = node.find(f"{_q('annotation')}/{_q('documentation')}")
        if doc is None:
            return None
        text = " ".join("".join(doc.itertext()).split())
        return text or None
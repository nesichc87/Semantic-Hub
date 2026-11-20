"""Configuration schemas for the generic source types (RDF, XSD).

A source is defined by configuration only. Predicates are given as
full IRIs or as prefixed names that are expanded with ``prefixes``.
They are evaluated as single predicates, never as SPARQL, so that
configurations submitted by users cannot inject queries.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PropertyConfig(BaseModel):
    """Predicates used to collect properties of a class via domain and inheritance."""

    model_config = ConfigDict(extra="forbid")

    domain: str
    superclass: str
    range: str
    description: str


class RDFSourceConfig(BaseModel):
    """Configuration of one generic RDF source."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    prefix: str = Field(min_length=1)
    namespace: str = Field(min_length=1)
    locations: list[str] = Field(min_length=1)
    format: Literal["turtle", "json-ld", "xml"]
    license: str | None = None
    prefixes: dict[str, str] = Field(default_factory=dict)
    types: list[str] = Field(default_factory=list)
    label: list[str] = Field(default_factory=list)
    description: list[str] = Field(default_factory=list)
    equivalence: list[str] = Field(default_factory=list)
    code_links: dict[str, str] = Field(default_factory=dict)
    languages: list[str | None] = Field(default_factory=lambda: ["en", None])
    language_order: Literal["strict", "merged"] = "strict"
    name_from: Literal["label", "label_or_local", "local_name"] = "label"
    whitespace: Literal["normalize", "strip"] = "normalize"
    id_separators: dict[str, str] = Field(default_factory=dict)
    compact: dict[str, str] = Field(default_factory=dict)
    properties: PropertyConfig | None = None

    def expand(self, name: str) -> str:
        """Return the full IRI for a full IRI or a prefixed name.

        A value containing "://" is taken as a full IRI. Any other value
        must be "prefix:local" with a prefix listed in ``prefixes``.
        """
        if "://" in name:
            return name
        prefix, separator, local = name.partition(":")
        if not separator or not local or prefix not in self.prefixes:
            raise ValueError(f"Cannot resolve predicate or type '{name}'")
        return self.prefixes[prefix] + local

    @model_validator(mode="after")
    def check_predicates(self) -> "RDFSourceConfig":
        """Reject configurations with predicates or types that cannot be resolved."""
        names = [
            *self.types,
            *self.label,
            *self.description,
            *self.equivalence,
            *self.code_links,
        ]
        if self.properties is not None:
            names += [
                self.properties.domain,
                self.properties.superclass,
                self.properties.range,
                self.properties.description,
            ]
        for name in names:
            self.expand(name)
        return self


class XSDSourceConfig(BaseModel):
    """Configuration of one generic XSD source.

    Concepts are the named global types of the main schema (and, with
    ``follow``, of included or imported schemas). ``prefix`` applies to the
    target namespace of the main schema; ``import_prefixes`` maps further
    target namespaces to prefixes.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    prefix: str = Field(min_length=1)
    location: str = Field(min_length=1)
    license: str | None = None
    kinds: list[Literal["complexType", "simpleType"]] = Field(
        default_factory=lambda: ["complexType", "simpleType"]
    )
    documentation: bool = False
    follow: bool = False
    import_prefixes: dict[str, str] = Field(default_factory=dict)
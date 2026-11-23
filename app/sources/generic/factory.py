"""Builds sources from catalog entries of the form {"type": ..., "config": {...}}."""

from collections.abc import Mapping

from app.sources.base import SemanticSource
from app.sources.generic.config_schema import (
    RDFSourceConfig,
    TableSourceConfig,
    XSDSourceConfig,
)
from app.sources.generic.rdf import Fetch, GenericRDFSource
from app.sources.generic.table import GenericTableSource
from app.sources.generic.xsd import GenericXSDSource

def create_source(entry: Mapping, fetch: Fetch) -> SemanticSource:
    """Validate a catalog entry and build the matching source without loading it.

    Raises ValueError for an unknown type or an invalid configuration
    (pydantic's ValidationError is a subclass of ValueError).
    """
    source_type = entry.get("type")
    config = entry.get("config")
    if config is None:
        raise ValueError("Catalog entry has no 'config'")
    if source_type == "rdf":
        return GenericRDFSource(RDFSourceConfig.model_validate(config), fetch)
    if source_type == "xsd":
        return GenericXSDSource(XSDSourceConfig.model_validate(config), fetch)
    if source_type == "table":
        return GenericTableSource(TableSourceConfig.model_validate(config), fetch)
    raise ValueError(f"Unknown source type: {source_type!r}")
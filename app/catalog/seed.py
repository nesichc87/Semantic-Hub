"""Seed list: sources shipped with the hub as an offer.

Nothing is activated automatically. A seed source is copied into the
catalog as approved when the admin activates it and confirms its license,
or at the first start (empty catalog) when its ID is listed in
SEMANTIC_HUB_SEED_SOURCES. The seed file is only read.
"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.catalog.repository import SourceCatalog, SourceRecord


DEFAULT_SEED_PATH = Path(__file__).parent / "seed.json"
SEED_VARIABLE = "SEMANTIC_HUB_SEED_SOURCES"


class SeedSource(BaseModel):
    """One shipped source: description, license and catalog entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    description: str
    license: str = Field(min_length=1)
    entry: dict


def load_seed(path: Path | str) -> list[SeedSource]:
    """Read and check the seed file; raises ValueError if it is invalid."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Seed file must contain a list: {path}")
    try:
        seeds = [SeedSource.model_validate(item) for item in data]
    except ValidationError as exc:
        raise ValueError(f"Invalid seed file {path}: {exc}") from exc

    seen: set[str] = set()
    for seed in seeds:
        if seed.id in seen:
            raise ValueError(f"Duplicate seed ID: {seed.id}")
        seen.add(seed.id)
        config = seed.entry.get("config")
        config_id = config.get("id") if isinstance(config, dict) else None
        if config_id != seed.id:
            raise ValueError(f"Seed ID '{seed.id}' differs from config ID '{config_id}'")
    return seeds


def activate_seed(
    catalog: SourceCatalog,
    seeds: Sequence[SeedSource],
    seed_id: str,
    license_confirmed: bool,
) -> SourceRecord:
    """Copy a seed source into the catalog as approved, with the seed's license."""
    seed = _find(seeds, seed_id)
    if not license_confirmed:
        raise ValueError(f"License of seed source '{seed_id}' must be confirmed: {seed.license}")
    catalog.add(seed.entry, license=seed.license)
    return catalog.set_status(seed.id, "approved")


def preselect_seed(
    catalog: SourceCatalog,
    seeds: Sequence[SeedSource],
    environ: Mapping[str, str],
) -> list[str]:
    """At the first start (empty catalog), activate the seed IDs from the environment.

    Setting the variable confirms the licenses of the listed sources.
    All IDs are checked before anything is activated.
    """
    requested = [part.strip() for part in environ.get(SEED_VARIABLE, "").split(",") if part.strip()]
    if not requested or catalog.list_sources():
        return []
    for seed_id in requested:
        _find(seeds, seed_id)
    for seed_id in requested:
        activate_seed(catalog, seeds, seed_id, license_confirmed=True)
    return requested


def _find(seeds: Sequence[SeedSource], seed_id: str) -> SeedSource:
    for seed in seeds:
        if seed.id == seed_id:
            return seed
    raise ValueError(f"Unknown seed source: {seed_id}")
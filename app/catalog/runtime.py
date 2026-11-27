"""Source catalog at application start: migrate, open, preselect seed sources.

A database or migration failure does not stop the application: the
catalog is then unavailable (``catalog`` is None) and the reason is kept
in ``error``. A failed preselection of seed sources is only logged.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine, create_engine, text

from app.catalog.db import upgrade_database
from app.catalog.repository import SourceCatalog
from app.catalog.seed import DEFAULT_SEED_PATH, load_seed, preselect_seed
from app.config import database_url


logger = logging.getLogger(__name__)

# Prefixes of the built-in sources, which are not part of the catalog yet.
BUILTIN_PREFIXES = ("kbl:", "vec:", "qudt:unit:", "dppo:")


@dataclass
class CatalogState:
    engine: Engine | None = None
    catalog: SourceCatalog | None = None
    error: str | None = None

    def close(self) -> None:
        if self.engine is not None:
            self.engine.dispose()


def init_catalog(
    environ: Mapping[str, str],
    seed_path: Path | str = DEFAULT_SEED_PATH,
) -> CatalogState:
    url = database_url(environ)
    try:
        upgrade_database(url)
        engine = create_engine(url, pool_pre_ping=True)
    except Exception as exc:
        logger.warning("Source catalog unavailable: %s", exc, exc_info=True)
        return CatalogState(error=f"{type(exc).__name__}: {exc}")

    catalog = SourceCatalog(engine, reserved_prefixes=BUILTIN_PREFIXES)
    try:
        preselect_seed(catalog, load_seed(seed_path), environ)
    except Exception as exc:
        logger.warning("Preselection of seed sources failed: %s", exc, exc_info=True)
    return CatalogState(engine=engine, catalog=catalog)


def check_database(state: CatalogState) -> bool:
    """True if the catalog database answers a trivial query."""
    if state.engine is None or state.catalog is None:
        return False
    try:
        with state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return False
    return True
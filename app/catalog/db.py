"""Database setup of the source catalog.

Migrations live in ``app/catalog/migrations`` (inside the package, so they
are part of the Docker image) and are run from code; no alembic.ini is needed.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config


MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def alembic_config(url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    # Config values use ConfigParser interpolation, so "%" must be doubled.
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def upgrade_database(url: str) -> None:
    """Bring the database at ``url`` to the latest migration."""
    command.upgrade(alembic_config(url), "head")
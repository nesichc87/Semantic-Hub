"""Alembic environment: runs migrations on the database from the config."""

from alembic import context
from sqlalchemy import create_engine, pool

from app.catalog.models import Base


config = context.config
target_metadata = Base.metadata


def run_migrations_online() -> None:
    engine = create_engine(config.get_main_option("sqlalchemy.url"), poolclass=pool.NullPool)
    with engine.connect() as connection:
        # Batch mode lets later migrations alter tables on SQLite as well.
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("Offline migrations are not supported")

run_migrations_online()
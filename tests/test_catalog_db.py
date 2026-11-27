from sqlalchemy import create_engine, inspect

from app.catalog.db import downgrade_database, upgrade_database


def sqlite_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'catalog.db').as_posix()}"


def table_columns(url: str) -> dict[str, set[str]]:
    engine = create_engine(url)
    try:
        inspector = inspect(engine)
        return {
            table: {column["name"] for column in inspector.get_columns(table)}
            for table in inspector.get_table_names()
        }
    finally:
        engine.dispose()


def test_upgrade_creates_catalog_tables(tmp_path):
    url = sqlite_url(tmp_path)

    upgrade_database(url)

    columns = table_columns(url)
    assert columns["sources"] == {
        "id",
        "type",
        "config",
        "prefixes",
        "status",
        "status_reason",
        "license",
        "created_at",
        "updated_at",
    }
    assert columns["source_loads"] == {
        "id",
        "source_id",
        "started_at",
        "finished_at",
        "outcome",
        "message",
        "from_cache",
    }


def test_upgrade_twice_is_harmless(tmp_path):
    url = sqlite_url(tmp_path)

    upgrade_database(url)
    upgrade_database(url)

    assert {"sources", "source_loads"} <= set(table_columns(url))

def test_downgrade_removes_catalog_tables(tmp_path):
    url = sqlite_url(tmp_path)
    upgrade_database(url)

    downgrade_database(url)

    assert not {"sources", "source_loads"} & set(table_columns(url))


def test_downgrade_of_empty_database_is_harmless(tmp_path):
    url = sqlite_url(tmp_path)

    downgrade_database(url)

    assert not {"sources", "source_loads"} & set(table_columns(url))
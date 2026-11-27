import os

import pytest

from app.catalog.db import downgrade_database


TEST_DATABASE_VARIABLE = "SEMANTIC_HUB_TEST_DATABASE_URL"


@pytest.fixture
def catalog_url(tmp_path):
    """Database URL for catalog tests.

    Uses SEMANTIC_HUB_TEST_DATABASE_URL if set (e.g. PostgreSQL in CI),
    otherwise a SQLite file in tmp_path. An external database is emptied
    before and after each test by undoing all migrations.
    """
    url = os.environ.get(TEST_DATABASE_VARIABLE)
    if not url:
        yield f"sqlite:///{(tmp_path / 'catalog.db').as_posix()}"
        return
    downgrade_database(url)
    yield url
    downgrade_database(url)
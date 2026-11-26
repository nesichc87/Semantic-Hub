from app.config import DEFAULT_DATABASE_URL, database_url


def test_default_is_sqlite_file_in_working_directory():
    assert DEFAULT_DATABASE_URL == "sqlite:///semantic-hub.db"
    assert database_url({}) == DEFAULT_DATABASE_URL


def test_empty_variable_uses_default():
    assert database_url({"SEMANTIC_HUB_DATABASE_URL": ""}) == DEFAULT_DATABASE_URL


def test_variable_overrides_default():
    url = "postgresql+psycopg://hub:secret@db:5432/hub"

    assert database_url({"SEMANTIC_HUB_DATABASE_URL": url}) == url
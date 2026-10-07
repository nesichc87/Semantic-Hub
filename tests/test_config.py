from app.config import source_url


DEFAULT_URL = "https://example.org/source.ttl"


def test_source_url_returns_default_when_variable_is_not_set():
    assert source_url({}, "SEMANTIC_HUB_TEST_URL", DEFAULT_URL) == DEFAULT_URL


def test_source_url_returns_value_from_environment():
    environ = {"SEMANTIC_HUB_TEST_URL": "file:///C:/sources/source.ttl"}

    assert (
        source_url(environ, "SEMANTIC_HUB_TEST_URL", DEFAULT_URL)
        == "file:///C:/sources/source.ttl"
    )


def test_source_url_returns_default_when_variable_is_empty():
    environ = {"SEMANTIC_HUB_TEST_URL": ""}

    assert source_url(environ, "SEMANTIC_HUB_TEST_URL", DEFAULT_URL) == DEFAULT_URL


def test_source_url_ignores_other_variables():
    environ = {"SEMANTIC_HUB_OTHER_URL": "file:///C:/sources/other.ttl"}

    assert source_url(environ, "SEMANTIC_HUB_TEST_URL", DEFAULT_URL) == DEFAULT_URL
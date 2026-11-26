from collections.abc import Mapping


def source_url(environ: Mapping[str, str], name: str, default: str) -> str:
    """
    Return the source URL configured in the environment variable `name`.

    Falls back to `default` if the variable is not set or empty.
    Local copies can be configured as file URLs (e.g. file:///C:/sources/x.ttl).
    """

    value = environ.get(name)

    if not value:
        return default

    return value


DATABASE_URL_VARIABLE = "SEMANTIC_HUB_DATABASE_URL"
DEFAULT_DATABASE_URL = "sqlite:///semantic-hub.db"


def database_url(environ: Mapping[str, str]) -> str:
    """
    Return the catalog database URL from SEMANTIC_HUB_DATABASE_URL.

    Falls back to a SQLite file in the working directory if the variable
    is not set or empty. PostgreSQL is used via a URL such as
    postgresql+psycopg://user:password@host:5432/name.
    """

    return source_url(environ, DATABASE_URL_VARIABLE, DEFAULT_DATABASE_URL)
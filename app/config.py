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
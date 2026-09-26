"""
Mapping from source data types to IEC 61360 data types.

Only mappings that can be derived reliably from the source type
are included. Ambiguous or unsupported types return None.
"""


IEC61360_TYPE_MAPPING = {
    "xs:string": "STRING",
    "string": "STRING",
    "xs:boolean": "BOOLEAN",
    "boolean": "BOOLEAN",
}


def map_data_type(data_type: str | None) -> str | None:
    """
    Map a source data type to an IEC 61360 data type.

    Returns None if the source type is unknown or cannot be
    mapped reliably without additional semantic information.
    """

    if data_type is None:
        return None

    normalized_type = data_type.strip()

    return IEC61360_TYPE_MAPPING.get(normalized_type)
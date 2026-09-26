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

IEC61360_DATA_TYPES = {
    "DATE",
    "STRING",
    "STRING_TRANSLATABLE",
    "INTEGER_MEASURE",
    "INTEGER_COUNT",
    "INTEGER_CURRENCY",
    "REAL_MEASURE",
    "REAL_COUNT",
    "REAL_CURRENCY",
    "BOOLEAN",
    "RATIONAL",
    "RATIONAL_MEASURE",
    "TIME",
    "TIMESTAMP",
    "IRI",
    "IRDI",
    "HTML",
    "BLOB",
    "FILE",
}


def map_data_type(data_type: str | None) -> str | None:
    """
    Map a source data type to a valid IEC 61360 data type.

    Returns None if the source type is unknown or cannot be
    mapped reliably without additional semantic information.
    """
    if data_type is None:
        return None

    normalized_type = data_type.strip()
    mapped_type = IEC61360_TYPE_MAPPING.get(normalized_type)

    if mapped_type not in IEC61360_DATA_TYPES:
        return None

    return mapped_type
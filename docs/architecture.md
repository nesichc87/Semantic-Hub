[← Back to README](../README.md)

# Architecture

The project follows a layered architecture that separates the REST API from semantic resolution, the individual semantic sources and the output formatting.

```
                 REST API (FastAPI)
                        │
                        ▼
                   API Routes
                        │
                        ▼
                Semantic Resolver
                        │
                        ▼
                Semantic Registry
                        │
      ┌────────────┬────┴───────┬────────────┐
      ▼            ▼            ▼            ▼
     KBL          VEC          QUDT         DPPO
    (XSD)        (OWL)        (TTL)        (OWL)
      │            │            │            │
      └────────────┴─────┬──────┴────────────┘
                         ▼
              Internal Semantic Model
         (concepts, properties, provenance)
                         │
                         ▼
                     Formatter
               (original / iec61360)
                         │
                         ▼
                   API response
```

Semantic sources are implemented behind a common interface and map their source information into the internal semantic model. Source provenance is kept in the model.

The formatters operate on the internal semantic model rather than on source-specific data. This is intended to allow additional sources to reuse the existing output formats. With VEC as a second, differently modelled source (OWL ontology instead of XSD, ontology-native property identifiers instead of composed ones), the existing formatters, resolver and API endpoints could be reused without changes. The same applied to QUDT and DPPO.

A mock source is additionally available for development and testing.

This allows the Semantic Hub to support additional semantic sources without requiring a separate REST service for every source.

## Request flow

```
HTTP Request
     │
     ▼
FastAPI / API Route
     │
     ▼
Semantic Resolver
     │
     ▼
Semantic Registry  →  responsible semantic source
     │
     ▼
Internal Semantic Model
     │
     ▼
Formatter (original / iec61360)
     │
     ▼
JSON Response
```

Example requests:

```
GET /api/resolve/kbl:Component?format=original
GET /api/resolve/kbl:Component?format=iec61360
```

If no format is given, `original` is used.

Response structure:

```
{
  "semantic_id": "kbl:Component",
  "format": "original",
  "result": { ... }
}
```

The content of `result` depends on the requested format. For `kbl:Component`, both formats return the 16 properties of the KBL type, including inherited elements.

In the `iec61360` format, only supported data types are mapped (currently `xs:string` → `STRING`, `xs:boolean` → `BOOLEAN`). Unsupported or complex types are returned with `data_type: null`; the property itself is kept.

Unknown semantic identifiers result in HTTP 404. If the responsible source cannot be loaded, the API returns HTTP 503.

## Source abstraction

Semantic sources implement a common interface (`app/sources/base.py`):

```python
class SemanticSource(ABC):

    @abstractmethod
    def can_resolve(self, semantic_id: str) -> bool:
        ...

    @abstractmethod
    def resolve(self, semantic_id: str) -> SemanticConcept:
        ...

    @abstractmethod
    def suggest(self, query: str) -> list[str]:
        ...
```

- `can_resolve()` is used by the Registry to determine which source is responsible for a semantic identifier.
- `resolve()` returns a concept of the internal semantic model (`SemanticConcept`) for an identifier.
- `suggest()` returns semantic identifiers matching a search query.

This avoids coupling the REST API directly to individual semantic dictionaries.

## Resolver

The Resolver is responsible for resolving a semantic identifier through the registered semantic sources.

```
Semantic ID
     │
     ▼
  Registry
     │
     ▼
 matching source
     │
     ▼
  Resolver
     │
     ▼
 semantic information
```

The resolver is intentionally separated from the HTTP layer so that the resolution logic can also be used independently of the REST API.

## Registry

The Registry maintains the available semantic sources.

A source is registered with the Registry:

```python
registry.register(source)
```

The Registry uses `can_resolve()` to determine which source is able to resolve a given semantic identifier.

For suggestions, the Registry delegates the search query to all registered sources and returns their results in registration order of the sources. The order within each source is kept, so each source ranks its own suggestions.

If a source fails (e.g. because its source data cannot be loaded), it is skipped and a warning is logged, so the suggestions of the other sources are still returned.

This provides an extensible mechanism for adding additional semantic resources.

## Formatter

The paper describes the use of a Formatter as part of the Retrieval Service. In this implementation, formatters convert a concept of the internal semantic model into an API representation. They operate on the internal model, not on source-specific data.

Two formats are currently available (`?format=` parameter):

### `original` (default)

Source-oriented, normalized representation of the internal semantic model, including properties, semantic identifiers, type references and source provenance.

This is not an unchanged serialization of the source (e.g. not the original KBL XSD).

### `iec61360`

Minimal IEC 61360-oriented representation. This is **not** a complete or conformant IEC 61360 implementation.

Output fields per concept and property:

| Field | Content |
|---|---|
| `semantic_id` | semantic identifier |
| `preferred_name` | name of the concept or property |
| `definition` | description, if available |
| `data_type` | mapped IEC 61360 data type, or `null` |
| `unit` | unit, if available |
| `source_of_definition` | source from the provenance, if available |

Concepts additionally contain their `properties` and a `data_type`. The concept's `data_type` is set for value types (e.g. KBL simple types, using their base type) and is `null` for concepts that are described by properties (e.g. KBL complex types, VEC and DPPO classes). It is mapped with the same rules as property data types.

Data type mapping (`app/formatter/iec61360_types.py`):

| Source type | IEC 61360 data type |
|---|---|
| `xs:string` / `string` | `STRING` |
| `xs:boolean` / `boolean` | `BOOLEAN` |
| all other types (numeric XSD types, complex types, unknown or missing types) | `null` |

Unsupported types are not guessed. Properties with an unsupported type are kept in the output and returned with `data_type: null`.

## Project structure

```
Semantic-Hub/
│
├── .github/
│   └── workflows/
│       └── tests.yml               # runs the tests on every push (GitHub Actions)
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── semantic.py         # REST endpoints (resolve, suggest)
│   │
│   ├── formatter/
│   │   ├── base.py                 # common formatter interface
│   │   ├── original.py             # source-oriented output
│   │   ├── iec61360.py             # IEC 61360-oriented output
│   │   └── iec61360_types.py       # data type mapping for IEC 61360 output
│   │
│   ├── models/
│   │   └── semantic.py             # internal semantic model
│   │
│   ├── registry/
│   │   └── registry.py             # registration of semantic sources
│   │
│   ├── resolver/
│   │   └── resolver.py             # resolution of semantic identifiers
│   │
│   ├── sources/
│   │   ├── base.py                 # common semantic source interface
│   │   ├── mock.py                 # mock source (development / testing)
│   │   ├── ranking.py              # ranking of suggestions (exact, prefix, substring)
│   │   ├── kbl/
│   │   │   ├── client.py           # loading of the KBL XSD
│   │   │   ├── parser.py           # XSD parsing
│   │   │   ├── service.py          # high-level resolution of KBL types and their elements
│   │   │   ├── mapper.py           # maps resolved types to the internal model
│   │   │   └── source.py           # KBL semantic source
│   │   ├── vec/
│   │   │   ├── client.py           # loading of the VEC ontology (Turtle)
│   │   │   ├── service.py          # resolution of VEC classes, properties and inheritance
│   │   │   ├── mapper.py           # maps resolved classes to the internal model
│   │   │   └── source.py           # VEC semantic source
│   │   ├── qudt/
│   │   │   ├── client.py           # loading of the QUDT unit vocabulary (Turtle)
│   │   │   ├── service.py          # resolution and search of QUDT units
│   │   │   ├── mapper.py           # maps resolved units to the internal model
│   │   │   └── source.py           # QUDT semantic source
│   │   └── dppo/
│   │       ├── client.py           # loading of the DPPO modules (Turtle) from a URL template
│   │       ├── service.py          # resolution and search of DPPO classes across modules
│   │       ├── mapper.py           # maps resolved classes to the internal model
│   │       └── source.py           # DPPO semantic source
│   │
│   ├── static/
│   │   ├── swagger/                # local copy of Swagger UI (swagger-ui-dist 5.17.14, Apache License 2.0)
│   │   └── ui/                     # demo page, served under /ui/
│   │       ├── index.html          # page structure
│   │       ├── i18n.js             # texts per language (de, en)
│   │       ├── ui.css              # colour and font tokens, light and dark theme
│   │       └── ui.js               # suggestions, resolution, property table, language switch
│   │
│   ├── config.py                   # source URL configuration via environment variables
│   └── main.py                     # FastAPI application, demo page and local Swagger UI
│
├── scripts/
│   └── start-demo.ps1              # offline start with local sources and warm-up
│
├── docs/                           # documentation (architecture, sources, API, development)
├── tests/                          # pytest test suite
├── LICENSE                         # Apache License 2.0
├── requirements.txt
└── README.md
```

The structure is intentionally modular so that semantic sources and formatting logic can be developed independently from the REST API.

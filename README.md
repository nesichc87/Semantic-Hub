# Semantic Hub

Prototype implementation of the **Semantic Hub** concept described in:

> **The Semantic Hub – Unifying Fragmented Semantic Dictionaries for Industry 4.0 and AAS**  
> Markus Rentschler et al.

The project aims to provide an open and extensible infrastructure for resolving and retrieving semantic information from different semantic sources in the context of **Industry 4.0** and the **Asset Administration Shell (AAS)**.

The implementation is developed based on the architecture and concepts described in the paper and is being built up incrementally from a clean implementation.

---

## Project Status

🚧 **Early development / Work in progress**

The project is currently in the initial architecture and API implementation phase.

Currently implemented:

- FastAPI-based REST API
- API routing
- Semantic resolver
- Semantic source registry
- Pluggable semantic source interface
- Initial mock semantic source
- OpenAPI / Swagger documentation

Planned functionality includes:

- KBL integration
- QUDT integration
- VEC integration
- Semantic source resolution
- Registry and source management
- Semantic data formatting
- IEC 61360 representation
- AAS-compatible semantic information
- Graphical user interface
- Docker-based deployment

---

## Architecture

The project follows a layered architecture intended to separate the REST API from semantic resolution and individual semantic sources.

```text
                    REST API
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
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
         KBL          QUDT         VEC
       Source        Source       Source
````
The individual semantic sources are intended to be implemented behind a common interface.

This allows the Semantic Hub to support additional semantic sources without requiring a separate REST service for every source.

---

## Current API Flow

The current prototype already implements the following flow:
```text
HTTP Request
     │
     ▼
FastAPI
     │
     ▼
API Route
     │
     ▼
Semantic Resolver
     │
     ▼
Semantic Registry
     │
     ▼
Semantic Source
     │
     ▼
Response
````
For the initial implementation, a mock semantic source is used to verify the architecture.

Example:
```text
GET /api/resolve/mock:123
````
Response:
```text
{
  "semantic_id": "mock:123",
  "result": {
    "semantic_id": "mock:123",
    "source": "mock",
    "name": "Example semantic concept"
  }
}
````
The mock source is only used for development and testing and will later be replaced or supplemented by real semantic sources.

---

## Project Structure

The current project structure is organized around the planned architecture:
```text
Semantic-Hub/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── semantic.py
│   │
│   ├── formatter/
│   │   └── iec61360.py
│   │
│   ├── registry/
│   │   └── registry.py
│   │
│   ├── resolver/
│   │   └── resolver.py
│   │
│   ├── sources/
│   │   ├── base.py
│   │   └── mock.py
│   │
│   └── main.py
│
├── tests/
│
├── requirements.txt
├── Dockerfile
└── README.md
````
The structure is intentionally modular so that semantic sources and formatting logic can be developed independently from the REST API.

---

## Semantic Sources

The Semantic Hub is intended to work with heterogeneous semantic resources.

The initial target sources are:

## KBL

KBL is planned as the first real semantic source integration.

The existing student prototype contains a KBL mapping implementation which will be used as a reference for the new implementation.

## QUDT

QUDT is planned as an additional semantic source.

The existing prototype uses SPARQL-based access to QUDT resources.

## VEC

VEC is also planned as a semantic source.

The implementation will be integrated through the common semantic source interface.

---

## Source Abstraction

Semantic sources implement a common interface.

Conceptually:
```text
class SemanticSource:

    def can_resolve(self, semantic_id: str) -> bool:
        ...

    def resolve(self, semantic_id: str):
        ...
````
The Registry uses this interface to determine which source can handle a given semantic identifier.

This avoids coupling the REST API directly to individual semantic dictionaries.

---

## Resolver

The Resolver is responsible for resolving a semantic identifier through the registered semantic sources.

Conceptually:
```text
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
````
The resolver is intentionally separated from the HTTP layer so that the resolution logic can also be used independently of the REST API.

---

## Registry

The Registry maintains the available semantic sources.

A source can be registered with the Registry:
```text
registry.register(source)
````
The Registry can then determine which source is able to resolve a given semantic identifier.

This provides an extensible mechanism for adding additional semantic resources.

---

## Formatter

The Semantic Hub is intended to transform information from different semantic sources into a common representation.

The paper describes the use of a Formatter as part of the Retrieval Service.

One important target representation is IEC 61360, which is relevant for AAS-based semantic descriptions.

The formatter implementation is currently only prepared as part of the project structure.

---

## REST API

The REST API is implemented using FastAPI.

The automatically generated API documentation is available through Swagger UI:
```text
/docs
````
The OpenAPI specification is available at:
```text
/openapi.json
````
### Current endpoints
#### Health
```text
GET /health
````
Returns the current application status.

#### Root
```text
GET /
````
Returns basic application information.

#### Semantic resolution
```text
GET /api/resolve/{semantic_id}
````
Resolves a semantic identifier using the registered semantic sources.

Example:
```text
GET /api/resolve/mock:123
````

---

## Docker

The Semantic Hub is intended to be deployed as a Docker container.

The application is therefore being developed with containerized deployment in mind from the beginning.

Planned deployment:
```text
Docker Container
┌──────────────────────────────┐
│                              │
│       Semantic Hub API       │
│                              │
│          FastAPI             │
│             │                │
│       Resolver / Registry    │
│             │                │
│        Semantic Sources      │
│                              │
└──────────────────────────────┘
````
The GUI and additional infrastructure may later be deployed as separate services using Docker Compose.

---

## Development

Install the Python dependencies:
```text
pip install -r requirements.txt
````
Start the development server:
```text
uvicorn app.main:app --reload
````
The API will then be available at:
```text
http://127.0.0.1:8000
````
Swagger UI:
```text
http://127.0.0.1:8000/docs
````
---

## Reference

The project is based on the concepts described in:
https://wwwlehre.dhbw-stuttgart.de/~rentschler/Publications/ETFA2026__The_Semantic_Hub_extended.pdf
Rentschler, M. et al.

The Semantic Hub – Unifying Fragmented Semantic Dictionaries for Industry 4.0 and AAS.

The paper proposes an open infrastructure for integrating heterogeneous semantic resources and describes a Retrieval Service consisting of components including a Registry, Resolver and Formatter.

The project uses these concepts as the architectural basis for the implementation.


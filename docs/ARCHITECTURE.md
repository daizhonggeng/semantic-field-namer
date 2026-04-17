# Architecture

## Backend

The backend is a FastAPI application with a small service-oriented layout:

- `api/routes`: HTTP endpoints
- `core`: config, database, auth, reserved words
- `services`: import parsing, normalization, embeddings, generation, Qdrant, LLM gateway
- `models`: SQLAlchemy models stored in SQLite

### Backend responsibilities

- Authentication and project isolation
- SQL / JSON schema import
- Style analysis
- Exact / lexical / semantic / LLM field generation
- Result persistence
- AI health reporting

## Frontend

The frontend is a React + Vite SPA with:

- route-based pages
- Ant Design UI
- TanStack Query for server state
- axios API client

### Main pages

- Login / Register
- Projects
- Import
- Style
- Generate
- Members
- History

## Data stores

- SQLite for relational state
- Qdrant for semantic retrieval

## Generation decision order

1. Normalize incoming Chinese field text
2. Exact mapping lookup
3. Lexical similarity lookup
4. Semantic vector retrieval
5. LLM fallback for unresolved items
6. Conflict and reserved-word correction

## Product constraint

The LLM is not the primary source of truth. The semantic mapping pool is.

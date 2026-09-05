# SatQuery AI Architecture

## Initial boundaries

- `frontend/` contains the React and TypeScript user interface.
- `backend/app/` contains the FastAPI application and runtime settings.
- `backend/app/ai/` is the boundary for model orchestration and evidence generation.
- `backend/app/search/` is the boundary for geospatial retrieval and search adapters.
- `config/` holds checked-in, non-secret configuration scaffolding.
- `.env.example` documents local environment variable names without real credentials.

## Direction

The API should expose stable application-level contracts while AI providers, search services,
and storage implementations remain replaceable behind the `ai` and `search` boundaries.
# ZHA-14 Backend Delivery Note

## Scope
- FastAPI backend skeleton under `backend/`
- PostgreSQL-oriented SQLAlchemy models + Alembic migration
- JWT auth endpoints (`/api/v1/auth/register`, `/api/v1/auth/login`)
- Core project and asset APIs under `/api/v1/projects`
- Local startup via `docker-compose.yml`

## Main contracts
- Projects are user-scoped and require Bearer token auth.
- `POST /api/v1/projects/{project_id}/assets` acts as upsert-by `(project_id, step_code, asset_type)` and appends a row to `asset_versions` on every write.
- `GET /api/v1/projects/{project_id}/steps` returns seeded progress records for the default writing pipeline.

## Compatibility / rollout
- Introduces a new backend service from scratch, so there is no runtime backward-compatibility burden yet.
- Migration `20260410_0001` is a base schema migration; rollback is `alembic downgrade -1`.
- SQLite is supported only for local/unit-test fallback; production target remains PostgreSQL.

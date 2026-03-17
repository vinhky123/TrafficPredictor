# shared/

Shared libraries intended to be reused across:

- `backend/` (API + ML wrapper)
- `airflow/` (ETL orchestration tasks)

In this portfolio refactor, the shared layer is kept minimal to avoid over-coupling. The legacy ETL code is preserved under `airflow/legacy-etl/` for reference.


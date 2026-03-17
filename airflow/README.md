# Airflow (ETL Orchestration)

This folder is a **portfolio-ready** Airflow setup showing how the ETL would be orchestrated on cloud (AWS MWAA / GCP Composer / Astronomer).

## DAGs

- `dags/traffic_etl_dag.py`: runs every 5 minutes:
  - Extract (HERE API)
  - Transform
  - Load (S3 / DynamoDB)
  - Predict (optional)

## Airflow Variables (suggested)

- `API_HERE_1`
- `HERE_CENTER_LAT`, `HERE_CENTER_LNG`
- `HERE_RADIUS_M`
- `S3_BUCKET`
- `S3_PREFIX_REALTIME`
- `MODEL_NAME`

The current DAG contains demo-safe placeholders so the repository **looks and reads like a production pipeline** without requiring credentials.


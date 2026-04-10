# Airflow — ETL Pipeline

Apache Airflow DAGs that orchestrate the traffic data pipeline from extraction to prediction.

## Pipeline Overview

```
HERE Traffic API ──→ Extract ──→ S3 (raw JSON)
                                    │
                                    ▼
                              Transform (PySpark)
                                    │
                                    ▼
                              S3 (Parquet)
                                    │
                                    ▼
                              Load → DocumentDB
                                    │
                                    ▼
                              Predict (Backend API)
```

## DAG: `traffic_etl`

| Task | Description |
|------|-------------|
| `extract` | Fetch real-time traffic flow from HERE API |
| `upload_raw` | Persist raw JSON snapshot to S3 |
| `transform` | PySpark: parse, filter, compute speed metrics, write Parquet |
| `load` | Upsert transformed records into DocumentDB/MongoDB |
| `predict` | Trigger TimeXer inference via backend `/api/db_notice` |

**Schedule:** Every 5 minutes (`*/5 * * * *`)

## Airflow Variables

Set these in the Airflow UI (`Admin → Variables`) or via Terraform:

| Variable | Description | Default |
|----------|-------------|---------|
| `HERE_API_KEY` | HERE Traffic Flow API key | `demo-key` |
| `HERE_CENTER_LAT` | Query circle latitude | `10.777195` |
| `HERE_CENTER_LNG` | Query circle longitude | `106.695364` |
| `HERE_RADIUS_M` | Query radius in metres | `20000` |
| `S3_BUCKET` | S3 bucket for raw/transformed data | `traffic-predictor-data` |
| `AWS_REGION` | AWS region | `ap-southeast-1` |
| `MONGODB_URI` | MongoDB/DocumentDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | Database name | `Traffic` |
| `BACKEND_URL` | Backend base URL for prediction trigger | `http://backend:5000` |

## Custom Operators

- **`HereTrafficExtractOperator`** (`plugins/operators/here_api_operator.py`) — reusable operator wrapping the HERE Traffic Flow API call.

## Local Development

Use the root `docker-compose.yml` to start Airflow alongside the backend and MongoDB:

```bash
docker compose up airflow-webserver airflow-scheduler
```

Airflow UI is available at `http://localhost:8080` (default credentials: `airflow` / `airflow`).
